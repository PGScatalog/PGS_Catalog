from django.contrib import admin
from django.utils.html import format_html
from django import forms
from django.urls import path
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.db import models, transaction
from django.utils import timezone
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.contrib.admin import DateFieldListFilter
# Register your models here.
from .models import *
from catalog.models import Publication
from curation_tracker.litsuggest import litsuggest_fileupload_to_annotation_imports, annotation_to_dict, dict_to_annotation_import, annotation_import_to_dict, CurationPublicationAnnotationImport
from django.contrib.auth.decorators import login_required
from functools import update_wrapper
from django.http import HttpResponse, JsonResponse
from django.core.serializers import serialize

from rest_framework.response import Response
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import JSONRenderer

from typing import List
import re
import datetime as dt
import sys

admin.site.site_header = "PGS Catalog - Curation Tracker"
admin.site.site_title = "PGS Catalog - Curation Tracker"
admin.site.index_title = "Welcome to PGS Catalog - Curation Tracker"

curation_tracker_db = 'curation_tracker'



#### Shared methods ####

def check_publication_exist(id: str) -> bool:
    ''' Check if the publication is already in the curation tracker DB '''
    if re.match('^\d+$', str(id)):
        queryset = CurationPublicationAnnotation.objects.using(curation_tracker_db).filter(PMID=id).count()
    else:
        queryset = CurationPublicationAnnotation.objects.using(curation_tracker_db).filter(doi=id).count()
    if queryset:
        return True
    else:
        return False


def check_study_name(study_name: str, num: int = 0) -> str:
    ''' Check that the study_name is unique. Otherwise it will add incremental number as suffix '''
    queryset = CurationPublicationAnnotation.objects.using(curation_tracker_db).filter(study_name=study_name)
    if num:
        queryset = queryset.exclude(num=num)
    count = queryset.count()
    if count:
        sn_list = CurationPublicationAnnotation.objects.using(curation_tracker_db).values_list('study_name',flat=True)
        num = 2
        new_study_name = f'{study_name}_{num}'
        while new_study_name in sn_list:
            num += 1
            new_study_name = f'{study_name}_{num}'
        study_name = new_study_name
    return study_name


def next_id_number(model: object) -> int:
    ''' Generate the new primary key value '''
    assigned = 1
    if len(model.objects.using(curation_tracker_db).all()) != 0:
        assigned = model.objects.using(curation_tracker_db).latest().pk + 1
    return assigned


#### Custom Form classes ####

class CsvImportForm(forms.Form):
    """ CSV Import form """
    csv_file = forms.FileField(label=format_html('CSV file <span style="color:#F00"><b>*</b></span>'))

class LitsuggestImportForm(forms.Form):
    """ Litsuggest Import form """
    litsuggest_file = forms.FileField(label=format_html('Litsuggest TSV file'))

class LitsuggestCommentForm(forms.Form):
    '''Unique form for applying a comment to all litsuggest studies of a single import'''
    comment = forms.CharField(label='Comment', 
                              help_text=format_html('<div class="help">eg: Litsuggest Automatic Weekly Digest (Sep 24 2023 To Sep 30 2023)</div>'),
                              required=True, 
                              widget=forms.Textarea(attrs={'rows':3}), 
                              initial='Litsuggest Automatic Weekly Digest')
    
class StudyNameField(forms.CharField):
    def validate(self, value):
        super().validate(value)
        count_study_name = CurationPublicationAnnotation.objects.using(curation_tracker_db).filter(study_name=value).count()
        if(count_study_name):
            raise ValidationError('Name already exists in the database')
        
class LitsuggestPreviewTableForm(forms.Form):
    '''Deprecated'''
    comment = forms.CharField(label='Comment', 
                              help_text=format_html('<div class="help">eg: Litsuggest Automatic Weekly Digest (Sep 24 2023 To Sep 30 2023)</div>'),
                              required=True, 
                              widget=forms.Textarea(attrs={'rows':3}), 
                              initial='Litsuggest Automatic Weekly Digest')

class LitsuggestPreviewForm(forms.ModelForm):
    '''Form for bulk editing and saving newly imported litsuggest studies'''
    class Meta:
        model = CurationPublicationAnnotation
        fields = ['PMID','study_name','title','journal','eligibility','eligibility_dev_score',
            'eligibility_eval_score','eligibility_description','curation_status','first_level_curation_status']

    def __init__(self, *args, triage_info, **kwargs):
        super(LitsuggestPreviewForm, self).__init__(*args, **kwargs)
        self.triage_info = triage_info

    PMID = forms.CharField(required=True, widget=forms.HiddenInput()) # PMID is shown as plain text but needed in the form for further validation/data import
    doi = forms.CharField(required=False, widget=forms.HiddenInput())
    study_name = StudyNameField(required=True, widget=forms.TextInput(attrs={"required": True, "size": 12}))
    title = forms.CharField(widget=forms.Textarea(attrs={'rows':4}))
    eligibility_description = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows':4,'cols':16}))
    triage_info:dict
    error:str
    skip_reason:str

class LitsuggestPreviewFormSet(forms.BaseFormSet):
    '''Formset for litsuggest imports bulk editing (requires LitsuggestPreviewForm)'''
    def get_form_kwargs(self, index):
        ''' Redefined so each form of the set can have different triage infos '''
        kwargs = super().get_form_kwargs(index)
        ti = None
        if 'triage_info' in kwargs:
            ti = kwargs['triage_info'][index]
        return {'triage_info': ti}
    
CurationPublicationAnnotationFormSet = forms.formset_factory(LitsuggestPreviewForm, formset=LitsuggestPreviewFormSet, extra=0)

class CurationPublicationAnnotationForm(forms.ModelForm):
    """ Custom Admin form """
    class Meta:
        model = CurationPublicationAnnotation
        help_texts = {
            'id': 'ID automatically assigned',
            'creation_date': 'Creation date automatically assigned',
            'eligibility': 'Eligibility automatically assigned (default: Yes)'
        }
        exclude = ()

    def clean(self):
        """ Used as a form validator (on some of the fields) """
        cleaned_data = super().clean()
        study_name = cleaned_data.get('study_name')
        doi = cleaned_data.get('doi')
        pmid = cleaned_data.get('PMID')
        author_sub = cleaned_data.get('author_submission')
        validation_error = {}
        # Numeric fields
        for field in ['PMID', 'year']:
            field_val = cleaned_data.get(field)
            if field_val:
                if type(field_val) != int:
                    validation_error[field] = "Only numeric value allowed for this field"
        # PGP ID
        pgp_id = cleaned_data.get('pgp_id')
        if pgp_id:
            try:
               publication_id = Publication.objects.get(id=pgp_id)
            except Publication.DoesNotExist:
               validation_error['pgp_id'] = f"{pgp_id} can't be found in the PGS Catalog database"

        # Missing doi and/or PMID
        if not pmid and not doi and not author_sub:
            error_msg = 'The doi or PubMed ID must be populated unless it is an author submission'
            validation_error['doi'] = error_msg
            validation_error['PMID'] = error_msg

        # New entry: check duplicated IDs
        if not self.instance.id:
            if pmid or doi or study_name:
                if pmid:
                    if check_publication_exist(pmid):
                        validation_error['PMID'] = f"PubMed ID '{pmid}' already exists in the database."
                if doi:
                    if check_publication_exist(doi):
                        validation_error['doi'] = f"doi '{doi}' already exists in the database."
                if study_name:
                    count_study_name = CurationPublicationAnnotation.objects.using(curation_tracker_db).filter(study_name=study_name).count()
                    if count_study_name:
                        validation_error['study_name'] = f"Study name '{study_name}' already exists in the database."

        # Raise error(s)
        if validation_error:
            raise forms.ValidationError(validation_error)



#### Admin classes ####

class MultiDBModelAdmin(admin.ModelAdmin):
    ''' Generic class to add Curation Tracker admin classes '''
    # A handy constant for the name of the alternate database.
    using = curation_tracker_db

    formfield_overrides = {
        models.TextField: {'widget': forms.Textarea(attrs={'rows':3, 'cols':90})}
    }

    def save_model(self, request, obj, form, change):
        # Tell Django to save objects to the 'other' database.
        obj.save(using=self.using)

    def delete_model(self, request, obj):
        # Tell Django to delete objects from the 'other' database
        obj.delete(using=self.using)

    def get_queryset(self, request):
        # Tell Django to look for objects on the 'other' database.
        return super().get_queryset(request).using(self.using)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Tell Django to populate ForeignKey widgets using a query
        # on the 'other' database.
        return super().formfield_for_foreignkey(db_field, request, using=self.using, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        # Tell Django to populate ManyToMany widgets using a query
        # on the 'other' database.
        return super().formfield_for_manytomany(db_field, request, using=self.using, **kwargs)


class CurationCuratorAdmin(MultiDBModelAdmin):
    ''' Curatior Admin class '''
    list_display = ("name",)
    list_filter = ('name',)
    ordering = ('name',)

class PublicationDateFilter(DateFieldListFilter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        today = dt.date.today()
        twoweeksago = today - dt.timedelta(days=14)

        self.links = list(self.links)
        self.links.insert(3, ('Past 2 weeks', {
            self.lookup_kwarg_since: str(twoweeksago),
            self.lookup_kwarg_until: str(today),
        }))

        # Past years
        for date in CurationPublicationAnnotation.objects.exclude(publication_date__year=today.year).dates('publication_date', 'year', order='ASC'):
            year = date.year
            year_start = dt.date(year,1,1)
            year_end = dt.date(year,12,31)
            self.links.insert(6, (year, {
                self.lookup_kwarg_since: str(year_start),
                self.lookup_kwarg_until: str(year_end),
            }))



class CurationPublicationAnnotationAdmin(MultiDBModelAdmin):
    ''' Publication Annotation Admin class (main class of the curation tracker) '''
    form = CurationPublicationAnnotationForm
    list_display = (
        "id","display_study_name","display_PMID","journal","publication_date","display_created_on","display_pgp_id",
        "curation_status","display_first_level_curation_status","display_first_level_curator",
        "display_second_level_curation_status","display_second_level_curator",
        "priority")
    list_filter = ("curation_status","first_level_curator","second_level_curator","priority",("publication_date",PublicationDateFilter),)
    search_fields = ["id","study_name","pgp_id","doi","PMID","first_level_curation_status","second_level_curation_status","curation_status","reported_trait"]
    ordering = ('-id',)
    list_per_page = 25 # No of records per page

    fieldsets = (
        ('Publication', {
            'fields': ("id","study_name","created_on","pgp_id",("doi","PMID"),("journal","year"),"title","publication_date","release_date","priority","author_submission","embargoed")
        }),
        ('Eligibility', {
            'fields': ("eligibility",("eligibility_dev_score","eligibility_eval_score"),("eligibility_external_valid","eligibility_trait_matching"),"eligibility_score_provided","eligibility_description")
        }),
        ('Curation - First Level', {
            'fields': ("first_level_curator",("first_level_curation_status","first_level_date"),"first_level_comment")
        }),
        ('Curation - Second Level', {
            'fields': ("second_level_curator",("second_level_curation_status","second_level_date"),"second_level_comment")
        }),
        ('Curation - Summary Status', {
            'fields': ("third_level_curator","curation_status")
        }),
        ('Other annotations', {
            'fields': ('reported_trait','gwas_and_pgs','comment')
        })
    )

    change_list_template = "curation_tracker/publication_changelist.html"


    def get_readonly_fields(self, request, obj=None):
        fields = ["id","creation_date","eligibility","release_date","created_on"]
        if obj:
            fields.append("num")
            if obj.first_level_curation_status == 'Determined ineligible':
                fields.append('second_level_curator')
                fields.append('second_level_curation_status')
                fields.append('second_level_date')
                fields.append('second_level_comment')
                fields.append('third_level_curator')
            elif obj.second_level_curation_status == 'Determined ineligible':
                fields.append('third_level_curator')
        return fields


    def display_pgp_id(self, obj):
        if obj.pgp_id:
            return format_html('<a href="/publication/{}">{}</a>',obj.pgp_id,obj.pgp_id)
        else:
            return None


    def display_study_name(self, obj):
        if obj.study_name:
            if obj.doi:
                if obj.doi.startswith('10'):
                    return format_html('<a href="https://doi.org/{}" target="_blank">{}</a>', obj.doi, obj.study_name)
            return obj.study_name
        else:
            return None

    def display_PMID(self, obj):
        if obj.PMID:
            return format_html('<a href="https://pubmed.ncbi.nlm.nih.gov/{}" target="_blank">{}</a>', obj.PMID, obj.PMID)
        else:
            return None
        
    def display_year(self, obj):
        if obj.year:
            return obj.year
        else:
            return None
    
    def display_first_level_curator(self, obj):
        if obj.first_level_curator:
            return obj.first_level_curator.name
        return '-'


    def display_first_level_curation_status(self, obj):
        if obj.first_level_curation_status:
            return obj.first_level_curation_status
        return None

    def display_second_level_curator(self, obj):
        if obj.second_level_curator:
            return obj.second_level_curator.name
        return None


    def display_second_level_curation_status(self, obj):
        if obj.second_level_curation_status:
            return obj.second_level_curation_status
        return None


    def display_third_level_curator(self, obj):
        if obj.third_level_curator:
            return obj.third_level_curator.name
        return None


    def display_created_on(self, obj):
        if obj.created_on:
            return obj.created_on.strftime('%b. %d, %Y')
        else:
            return None


    def save_model(self, request, obj, form, change):
        ''' Custom method to save the model into the curation tracker database. Overwrite the default method'''
        update_via_epmc = False

        # Eligibility - part 1
        if (obj.eligibility_dev_score == 'y' and obj.eligibility_external_valid == 'n') or \
           (obj.eligibility_dev_score == 'n' and obj.eligibility_eval_score == 'n') or \
            obj.eligibility_trait_matching == 'unmatched':
            obj.eligibility = False
        else:
            obj.eligibility = True

        if obj.eligibility == False:
            obj.first_level_curation_status = 'Determined ineligible'
            obj.curation_status = 'Abandoned/Ineligible'


        ## Model data updates before saving it in the database
        db_obj = None
        if not obj.num:
            # Primary key needs to be assigned for a new entry
            obj.set_annotation_ids(next_id_number(CurationPublicationAnnotation))
            obj.set_creation_date()
            obj.created_by = request.user
            obj.created_on = timezone.now()
            # Check if the Publication info can be populated via EuropePMC
            if obj.PMID or obj.doi:
                update_via_epmc = True
        else:
            # Deal with the change(s) on curation status for an existing entry
            db_obj = CurationPublicationAnnotation.objects.using(curation_tracker_db).get(num=obj.num)


        if not db_obj or db_obj.curation_status not in ('Released', 'Retired'):

            # Eligibility - revert ineligibility
            if db_obj and db_obj.eligibility == False and obj.eligibility == True:
                if obj.curation_status == 'Abandoned/Ineligible':
                    if obj.first_level_curation_status != 'Determined ineligible' and obj.second_level_curation_status != 'Determined ineligible':
                        obj.curation_status = 'Awaiting L1' # Back to default value

            # First level curation
            if obj.first_level_curation_status and (not db_obj or db_obj.first_level_curation_status != obj.first_level_curation_status):
                if obj.first_level_curation_status.startswith('Curation'):
                    if obj.second_level_curation_status == '-' or not obj.second_level_curation_status:
                        obj.second_level_curation_status = 'Awaiting curation'

                elif obj.first_level_curation_status.startswith('Pending'):
                    obj.curation_status = 'Pending author response'
                elif obj.first_level_curation_status == 'Determined ineligible':
                    obj.curation_status = 'Abandoned/Ineligible'

            # Second level curation
            elif obj.second_level_curation_status and (not db_obj or db_obj.second_level_curation_status != obj.second_level_curation_status):
                if obj.second_level_curation_status.startswith('Curation'):
                    obj.curation_status = 'Curated - Awaiting Import'
                elif obj.second_level_curation_status == 'Pending author response':
                    obj.curation_status = 'Pending author response'
                elif obj.second_level_curation_status == 'Determined ineligible':
                    obj.curation_status = 'Abandoned/Ineligible'
                elif obj.second_level_curation_status == 'Awaiting curation':
                    obj.curation_status = 'Awaiting L2'
                else:
                    obj.curation_status = 'Awaiting L1'

            # Desembargo the study
            if obj.embargoed == False and (not db_obj or db_obj.embargoed == True):
                if obj.curation_status == 'Embargo Imported - Awaiting Release':
                    if obj.doi or obj.PMID:
                        obj.curation_status = 'Imported - Awaiting Release'
                elif obj.curation_status == 'Embargo Curated - Awaiting Import':
                    obj.curation_status = 'Curated - Awaiting Import'

            # Check if the Publication info need to be updated via EuropePMC
            if db_obj and (obj.PMID != db_obj.PMID or obj.doi != db_obj.doi) \
                or (obj.PMID and (not obj.title or not obj.journal or not obj.doi)) \
                or (obj.doi and (not obj.title or not obj.journal or not obj.PMID)):
                update_via_epmc = True

            # Embargoed status
            if obj.embargoed == True:
                if obj.curation_status == 'Curated - Awaiting Import':
                    obj.curation_status = 'Embargo Curated - Awaiting Import'
                elif obj.curation_status == 'Imported - Awaiting Release':
                    obj.curation_status == 'Embargo Imported - Awaiting Release'

            # Eligibility - part 2
            if obj.curation_status == 'Abandoned/Ineligible':
                obj.eligibility = False

        # Update/Populate Publication info via EuropePMC (if available)
        if update_via_epmc:
            obj.get_epmc_data(keep_study_name=True)
            obj.study_name = check_study_name(obj.study_name, num = obj.num)

         # Timestamp
        obj.last_modified_by = request.user
        obj.last_modified_on = timezone.now()

        # Save new/updated model to the DB
        obj.save(using=self.using)


    def get_urls(self):        
        urls = super().get_urls()
        my_urls = [
            path('import-csv/', login_required(self.import_csv, login_url='/admin/login/')),
            path('import-litsuggest/', login_required(self.import_litsuggest, login_url='/admin/login/')),
            path('import-litsuggest/confirm_preview', login_required(self.confirm_litsuggest_preview, login_url='/admin/login/')),
            path('import-litsuggest/confirm_formset', login_required(self.confirm_litsuggest_formset, login_url='/admin/login/')),
            path('<path:object_id>/contact-author/', login_required(self.contact_author, login_url='/admin/login/'))
        ]
        return my_urls + urls
    
    
    def contact_author(self, request, object_id):

        def get_EPMC_Full_data(pmid):
            payload = {
                'format': 'json',
                'resultType': 'core', # for getting full journal name
                'query': f'ext_id:{str(pmid)}'
                }
            result = requests.get(constants.USEFUL_URLS['EPMC_REST_SEARCH'], params=payload)
            result = result.json()
            if 'result' in result['resultList']:
                result = result['resultList']['result'][0]
                return result
            else:
                raise Exception(f'No EPMC entry for {str(pmid)}')
            
        data = {}
        
        try:

            model = CurationPublicationAnnotation.objects.using(curation_tracker_db).get(num=object_id)
            publication_title = model.title.rstrip('.') if model.title else '&lt;Missing title&gt;'
            publication_year = str(model.year) if model.year else '&lt;Missing year&gt;'

            user = request.user
            user_name = ' '.join([user.first_name,user.last_name])

            if not model.PMID:
                raise Exception('No PMID')

            epmc_data = get_EPMC_Full_data(model.PMID)
            first_author_name = epmc_data['authorList']['author'][0]['lastName']
            full_journal_name = epmc_data['journalInfo']['journal']['title']

            if not user_name.strip():
                user_name = '&lt;Missing user name&gt;'
            if not first_author_name.strip():
                first_author_name = '&lt;Missing first author name&gt;'
            if not full_journal_name.strip():
                full_journal_name = '&lt;Missing journal name&gt;'

            template = EmailTemplate.objects.using(curation_tracker_db).get(template_type='author_data_request',is_default=True)
            email_body_template = template.body
            email_subject_template = template.subject

            email_body = email_body_template.replace('$$JOURNAL.NAME$$',full_journal_name.title())
            email_body = email_body.replace('$$PUBLICATION.PMID$$',str(model.PMID))
            email_body = email_body.replace('$$PUBLICATION.TITLE$$',publication_title)
            email_body = email_body.replace('$$PUBLICATION.YEAR$$',publication_year)
            email_body = email_body.replace('$$USER.NAME$$',user_name)
            email_body = email_body.replace('$$AUTHOR.NAME$$', first_author_name)

            email_subject = email_subject_template.replace('$$JOURNAL.NAME$$',full_journal_name.title())
            email_subject = email_subject.replace('$$PUBLICATION.PMID$$',str(model.PMID))
            email_subject = email_subject.replace('$$PUBLICATION.TITLE$$',publication_title)
            email_subject = email_subject.replace('$$PUBLICATION.YEAR$$',publication_year)
            email_subject = email_subject.replace('$$USER.NAME$$',user_name)
            email_subject = email_subject.replace('$$AUTHOR.NAME$$', first_author_name)

            data = {
                'email_subject': email_subject,
                'email_body': email_body
            }
        
        except EmailTemplate.DoesNotExist as e:
            data = {
                'error': 'No template found for author data request.'
            }

        except CurationPublicationAnnotation.DoesNotExist as e:
            data = {
                'error': 'No annotation found with this ID.'
            }

        except Exception as e:
            print(e, file=sys.stderr)
            data = {
                'error': str(e)
            }

        return JsonResponse(data)


    def import_csv(self, request):
        if request.method == "POST":
            csv_file = request.FILES["csv_file"]
            file_data = csv_file.read().decode('utf-8')
            cvs_data = file_data.split('\n')
            msg = ''
            with transaction.atomic():
                for line in cvs_data:
                    study_id = line.split('\t')[0]
                    if study_id != '':
                        print(f"\n# Data: {study_id}")
                        if check_publication_exist(study_id):
                            msg = msg + f"<br/>&#10060; - '{study_id}' already exists in the database - no import"
                        else:
                            # Create new model
                            model = CurationPublicationAnnotation()
                            model.set_annotation_ids(next_id_number(CurationPublicationAnnotation))
                            model.set_creation_date()
                            setattr(model,'study_name',study_id)

                            # Update model with EuropePMC data
                            if re.match('^\d+$', study_id):
                                model.PMID = study_id
                            else:
                                model.doi = study_id
                            has_epmc_data = model.get_epmc_data()
                            model.study_name = check_study_name(model.study_name)

                            # Save model in DB
                            model.save(using=curation_tracker_db)

                            if has_epmc_data:
                                msg = msg + f"<br/>&#10004; - '{study_id}' has been successfully imported in the database"
                            else:
                                msg = msg + f"<br/>&#10004; - '{study_id}' has been imported in the database but extra information couldn't be extracted from EuropePMC"

            self.message_user(request,  format_html(f"Your csv file has been imported{msg}"))
            return HttpResponseRedirect('..')

        form = CsvImportForm()
        payload = {"form": form}
        return render(
            request, "curation_tracker/csv_form.html", payload
        )
    
    def import_litsuggest_to_table(self,request):
        '''Deprecated'''
        if request.method == "POST":
            litsuggest_file = request.FILES["litsuggest_file"]
            models = litsuggest_fileupload_to_annotation_imports(litsuggest_file)

            preview_data = list(map(annotation_import_to_dict,models))
            request.session['preview_data'] = preview_data
            
            return render(
                request, "curation_tracker/litsuggest_preview_table.html", {
                    'annotations': preview_data,
                    'form': LitsuggestPreviewTableForm()
                }
            )

        form = LitsuggestImportForm()
        payload = {"form": form}
        return render(
            request, "curation_tracker/litsuggest_form.html", payload
        )

    def import_litsuggest(self,request):
        if request.method == "POST":
            litsuggest_file = request.FILES["litsuggest_file"]
            import_models = litsuggest_fileupload_to_annotation_imports(litsuggest_file)

            skipped_publications: List[dict] = [] # as dict so it can be serialized in session
            staged_publications_data: List[dict] = [] # format for FormSet 'initial' parameter
            triage_info: List[dict] = []

            for import_model in import_models:
                if import_model.error:
                    skipped_publications.append(annotation_import_to_dict(import_model))
                elif import_model.skip_reason:
                    skipped_publications.append(annotation_import_to_dict(import_model))
                else:
                    annotation = import_model.annotation
                    staged_publications_data.append(annotation_to_dict(annotation))
                    triage_info.append(import_model.triage_info)

            formset = CurationPublicationAnnotationFormSet(initial=staged_publications_data, form_kwargs={'triage_info':triage_info})
            # Keeping info in the session for reusing in the form if not valid
            request.session['skipped_publications'] = skipped_publications
            request.session['triage_info'] = triage_info                   
            
            return render(
                request, "curation_tracker/litsuggest_preview_form.html", {
                    'skipped_publications': skipped_publications,
                    'comment_form': LitsuggestCommentForm,
                    'formset': formset
                }
            )
        
        else:
            form = LitsuggestImportForm()
            payload = {"form": form}
            return render(
                request, "curation_tracker/litsuggest_form.html", payload
            )
        
    def confirm_litsuggest_preview(self,request):
        '''Deprecated'''
        if request.method == "POST":
            form = LitsuggestPreviewTableForm(request.POST)
            comment = None
            if form.is_valid():
                comment = form.cleaned_data['comment']
            preview_data = request.session['preview_data']
            del request.session['preview_data']
            annotations = list(map(dict_to_annotation_import, preview_data))
            with transaction.atomic():
                for annotation in annotations:
                    if annotation.is_valid() and annotation.is_importable():
                        annotation.annotation.comment = comment
                        annotation.save(using=curation_tracker_db)
            return HttpResponseRedirect('/admin/curation_tracker/curationpublicationannotation')
        
    def confirm_litsuggest_formset(self,request):
        if request.method == "POST":
            has_errors = False
            comment_form = LitsuggestCommentForm(request.POST)
            comment = None
            if comment_form.is_valid():
                comment = comment_form.cleaned_data['comment']
            else:
                has_errors = True

            triage_info = request.session.get('triage_info', []) # fetching triage infos for the formset in case it needs to be provided to the context again in case of error
            formset = CurationPublicationAnnotationFormSet(request.POST, form_kwargs={'triage_info':triage_info})
            annotation_imports: List[CurationPublicationAnnotationImport] = []
            if formset.is_valid() and not has_errors:
                for f in formset:
                    data = f.cleaned_data
                    data['comment'] = comment
                    annotation_import = dict_to_annotation_import({'model':data})
                    annotation_imports.append(annotation_import)
                with transaction.atomic():
                    [annotation_import.save() for annotation_import in annotation_imports]
            else:
                has_errors = True

            if has_errors:
                return render(
                    request, "curation_tracker/litsuggest_preview_form.html", {
                        'skipped_publications': request.session.get('skipped_publications', []),
                        'comment_form': comment_form,
                        'formset': formset
                    }
            )

            del request.session['skipped_publications']
            del request.session['triage_info']

        return HttpResponseRedirect('/admin/curation_tracker/curationpublicationannotation')
            
    display_pgp_id.short_description = 'PGP ID'
    display_study_name.short_description = 'Study Name'
    display_PMID.short_description = 'Pubmed ID'
    display_year.short_description = 'Year'
    display_year.admin_order_field = 'year'
    display_first_level_curator.short_description = 'L1 Curator'
    display_first_level_curation_status.short_description = 'L1 Curation Status'
    display_second_level_curator.short_description = 'L2 Curator'
    display_second_level_curation_status.short_description = 'L2 Curation Status'
    display_third_level_curator.short_description = 'L3 Curator'
    display_created_on.short_description = 'Creation Date'
    display_created_on.admin_order_field = 'created_on'

    # Batch actions
    actions = ["mark_as_released"]

    @admin.action(permissions=["change"],description="Mark selected studies as Released")
    def mark_as_released(self, request, queryset):
        queryset.update(curation_status='Released')


### Email Templates ###
class EmailTemplateForm(forms.ModelForm):
    class Meta:
        model = EmailTemplate
        widgets = {
            'body': forms.Textarea(attrs={'cols': 100, 'rows': 50}),
        }
        exclude = ('created_on','created_by','last_modified_on','last_modified_by')
        help_texts = {
            'body': 'Available tokens: PUBLICATION.TITLE, PUBLICATION.PMID, PUBLICATION.YEAR, AUTHOR.NAME, JOURNAL.NAME, USER.NAME'
        }

class EmailTemplateAdmin(MultiDBModelAdmin):
    form = EmailTemplateForm
    list_display = ("__str__","is_default","created_on","last_modified_on")
    fieldsets = (
        (None, {
         'fields': (('template_type','is_default'),'subject','body')
        }),
    )

    @transaction.atomic
    def save_model(self, request, obj:EmailTemplate, form, change):
        if not obj.id:
            obj.created_by = request.user
            obj.created_on = timezone.now()

        obj.last_modified_by = request.user
        obj.last_modified_on = timezone.now()

        # If default, set others not default
        if obj.is_default:
            templates = EmailTemplate.objects.using(curation_tracker_db).filter(template_type=obj.template_type)
            if(obj.id):
                templates = templates.exclude(id=obj.id)
            templates.update(is_default=False)

        super().save_model(request, obj, form, change)


admin.site.register(CurationCurator, CurationCuratorAdmin)
admin.site.register(CurationPublicationAnnotation, CurationPublicationAnnotationAdmin)
admin.site.register(EmailTemplate, EmailTemplateAdmin)