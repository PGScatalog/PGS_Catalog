from django.contrib import admin
from django.utils.html import format_html
from django import forms
from django.urls import path,reverse
from django.shortcuts import render
from django.http import HttpResponseRedirect
import csv
import re
from django import forms
from django.forms import TextInput, Textarea
from django.db import models
# Register your models here.
from .models import *
from catalog.models import Publication



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


def check_study_name(study_name: str) -> str:
    ''' Check that the study_name is unique. Otherwise it will add incremental number as suffix '''
    queryset = CurationPublicationAnnotation.objects.using(curation_tracker_db).filter(study_name=study_name).count()
    if queryset:
        sn_list = CurationPublicationAnnotation.objects.using(curation_tracker_db).values_list('study_name',flat=True)
        num = 1
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


class CurationPublicationAnnotationForm(forms.ModelForm):
    """ Custom Admin form """
    class Meta:
        model = CurationPublicationAnnotation
        help_texts = {
            'id': 'ID automatically assigned',
            'eligibility': 'Eligibility automatically assigned (default: Yes)'
        }
        exclude = ()

    def clean(self):
        """ Used as a form validator (on some of the fields) """
        study_name = self.cleaned_data['study_name']
        doi = self.cleaned_data['doi']
        pmid = self.cleaned_data['PMID']
        author_sub = self.cleaned_data['author_submission']
        validation_error = {}
        # Numeric fields
        for field in ['PMID', 'year']:
            field_val = self.cleaned_data[field]
            if field_val:
                if type(field_val) != int:
                    validation_error[field] = "Only numeric value allowed for this field"
        # PGP ID
        pgp_id = self.cleaned_data['pgp_id']
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
        models.TextField: {'widget': Textarea(attrs={'rows':3, 'cols':90})}
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


class CurationPublicationAnnotationAdmin(MultiDBModelAdmin):
    ''' Publication Annotation Admin class (main class of the curation tracker) '''
    form = CurationPublicationAnnotationForm
    list_display = (
        "id","study_name","display_doi","display_PMID","display_pgp_id",
        "display_first_level_curator","display_first_level_curation_status",
        "display_second_level_curator","display_second_level_curation_status","display_level_curation_comment",
        "display_third_level_curator","curation_status","priority","reported_trait")
    list_filter = ("curation_status","first_level_curator","second_level_curator","priority")
    search_fields = ["id","study_name","pgp_id","doi","PMID","first_level_curation_status","second_level_curation_status","curation_status","reported_trait"]
    ordering = ('-id',)

    fieldsets = (
        ('Publication', {
            'fields': ("id","study_name","pgp_id","doi","PMID",("journal","year"),"title","release_date","priority","author_submission","embargoed")
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
        if obj:
            fields = ["num","id","eligibility"]
            if obj.first_level_curation_status == 'Determined ineligible':
                fields.append('second_level_curator')
                fields.append('second_level_curation_status')
                fields.append('second_level_date')
                fields.append('second_level_comment')
                fields.append('third_level_curator')
            elif obj.second_level_curation_status == 'Determined ineligible':
                fields.append('third_level_curator')
            return fields
        else:
            return ["id","eligibility"]


    def display_doi(self, obj):
        if obj.doi:
            if obj.doi.startswith('10'):
                return format_html('<a href="https://doi.org/{}">{}</a>', obj.doi, obj.doi)
        return obj.doi


    def display_PMID(self, obj):
        if obj.PMID:
            if re.match('^\d+$', str(obj.PMID)):
                return format_html('<a href="https://europepmc.org/abstract/MED/{}">{}</a>', obj.PMID, obj.PMID)
        return obj.PMID


    def display_pgp_id(self, obj):
        if obj.pgp_id:
            return format_html('<a href="/publication/{}">{}</a>',obj.pgp_id,obj.pgp_id)
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


    def display_level_curation_comment(self, obj):
        comments = ''
        if obj.first_level_curator and obj.first_level_comment != '':
            comments = comments+obj.first_level_curator.name + ' (L1): ' + obj.first_level_comment
        if obj.second_level_curator and obj.second_level_comment != '':
            if comments != '':
                comments = comments + '\n'
            comments = comments + obj.second_level_curator.name + ' (L2): ' + obj.second_level_comment
        return comments


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
        if not obj.num:
            # Primary key needs to be assigned for a new entry
            obj.set_annotation_ids(next_id_number(CurationPublicationAnnotation))
            # Check if the Publication info can be populated via EuropePMC
            if obj.PMID or obj.doi:
                update_via_epmc = True
        else:
            # Deal with the change(s) on curation status for an existing entry
            db_obj = CurationPublicationAnnotation.objects.using(curation_tracker_db).get(num=obj.num)

            if db_obj.curation_status not in ('Released', 'Retired'):

                # Eligibility - revert ineligibility
                if obj.eligibility == True and db_obj.eligibility == False:
                    if obj.curation_status == 'Abandoned/Ineligible':
                        if obj.first_level_curation_status != 'Determined ineligible' and obj.second_level_curation_status != 'Determined ineligible':
                            obj.curation_status = 'Awaiting L1' # Back to default value

                # First level curation
                if obj.first_level_curation_status and db_obj.first_level_curation_status != obj.first_level_curation_status:
                    if obj.first_level_curation_status.startswith('Curation'):
                        if obj.second_level_curation_status == '-' or not obj.second_level_curation_status:
                            obj.second_level_curation_status = 'Awaiting curation'

                    elif obj.first_level_curation_status.startswith('Pending'):
                        obj.curation_status = 'Pending author response'
                    elif obj.first_level_curation_status == 'Determined ineligible':
                        obj.curation_status = 'Abandoned/Ineligible'

                # Second level curation
                elif obj.second_level_curation_status and db_obj.second_level_curation_status != obj.second_level_curation_status:
                    if obj.second_level_curation_status.startswith('Curation'):
                        obj.curation_status = 'Curated - Awaiting Import'
                    elif obj.second_level_curation_status == 'Pending author response':
                        obj.curation_status = 'Pending author response'
                    elif obj.second_level_curation_status == 'Determined ineligible':
                        obj.curation_status = 'Abandoned/Ineligible'
                    elif obj.second_level_curation_status == 'Awaiting curation':
                        obj.curation_status = 'Awaiting L1'
                    else:
                        obj.curation_status = 'Awaiting L2'

                # Desembargo the study
                if obj.embargoed == False and db_obj.embargoed == True:
                    if obj.curation_status == 'Embargo Imported - Awaiting Release':
                        if obj.doi or obj.PMID:
                            obj.curation_status = 'Imported - Awaiting Release'
                    elif obj.curation_status == 'Embargo Curated - Awaiting Import':
                        obj.curation_status = 'Curated - Awaiting Import'

                # Check if the Publication info need to be updated via EuropePMC
                if (obj.PMID != db_obj.PMID or obj.doi != db_obj.doi) \
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
            obj.get_epmc_data()
            obj.study_name = check_study_name(obj.study_name)

        # Save new/updated model to the DB
        obj.save(using=self.using)


    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('import-csv/', self.import_csv),
        ]
        return my_urls + urls


    def import_csv(self, request):
        if request.method == "POST":
            csv_file = request.FILES["csv_file"]
            file_data = csv_file.read().decode('utf-8')
            cvs_data = file_data.split('\n')
            msg = ''
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
                        setattr(model,'study_name',study_id)
                        # for field in pub_data.keys():
                        #     setattr(model, field, pub_data[field])

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


    display_pgp_id.short_description = 'PGP ID'
    display_doi.short_description = 'DOI'
    display_PMID.short_description = 'PubMed ID'
    display_first_level_curator.short_description = 'L1 Curator'
    display_first_level_curation_status.short_description = 'L1 Curation Status'
    display_second_level_curator.short_description = 'L2 Curator'
    display_second_level_curation_status.short_description = 'L2 Curation Status'
    display_level_curation_comment.short_description = 'L1 & L2 Curation Comments'
    display_third_level_curator.short_description = 'L3 Curator'



admin.site.register(CurationCurator, CurationCuratorAdmin)
admin.site.register(CurationPublicationAnnotation, CurationPublicationAnnotationAdmin)
