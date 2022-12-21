from django.contrib import admin
from django.utils.html import format_html
from django import forms
from django.urls import path,reverse
from django.shortcuts import render
from django.http import HttpResponseRedirect
import requests
import csv
import re
from django.forms import TextInput, Textarea
from django.db import models
# Register your models here.
from .models import *


admin.site.site_header = "PGS Catalog - Curation Tracker"
admin.site.site_title = "PGS Catalog - Curation Tracker"
admin.site.index_title = "Welcome to PGS Catalog - Curation Tracker"

curation_tracker_db = 'curation_tracker'
curation_admin_path = '/curation_admin/curation_tracker'
curation_annotation_path = curation_admin_path+'/curationpublicationannotation'
curation_publication_path = curation_admin_path+'/curationpublication'

tracker_db = 'curation_tracker'


def query_epmc(id):
    payload = {'format': 'json'}
    if re.match('^\d+$', id):
        query = f'ext_id:{id}'
    else:
        query = f'doi:{id}'
    payload['query'] = query
    result = requests.get('https://www.ebi.ac.uk/europepmc/webservices/rest/search', params=payload)
    result = result.json()
    result = result['resultList']['result'][0]
    return result


def check_publication_exist(id):
    if re.match('^\d+$', id):
        queryset = CurationPublicationAnnotation.objects.using(curation_tracker_db).filter(PMID=id)
    else:
        queryset = CurationPublicationAnnotation.objects.using(curation_tracker_db).filter(doi=id)
    if queryset:
        return True
    else:
        return False


def next_id_number(model):
    ''' Fetch the new primary key value. '''
    assigned = 1
    if len(model.objects.using(tracker_db).all()) != 0:
        assigned = model.objects.using(tracker_db).latest().pk + 1
    return assigned


class MultiDBModelAdmin(admin.ModelAdmin):
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


class CsvImportForm(forms.Form):
    csv_file = forms.FileField(label=format_html('CSV file <span style="color:#F00"><b>*</b></span>'))


class CurationCuratorAdmin(MultiDBModelAdmin):
    list_display = ("name",)
    list_filter = ('name',)
    ordering = ('name',)


class CurationPublicationAnnotationAdmin(MultiDBModelAdmin):
    list_display = (
        "id","study_name","display_doi","display_PMID","display_pgp_id",
        "display_first_level_curator","display_first_level_curation_status",
        "display_second_level_curator","display_second_level_curation_status","display_level_curation_comment",
        "display_third_level_curator","curation_status","reported_trait")
    list_filter = ("curation_status",)
    ordering = ('-id',)

    fieldsets = (
        ('Publication', {
            'fields': ("id","study_name","pgp_id","doi","PMID","journal","title","year","release_date","author_submission","embargoed")
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
        ('Curation - Third Level', {
            'fields': ("third_level_curator","curation_status")
        }),
        ('Other annotation', {
            'fields': ('reported_trait','gwas_and_pgs','comment')
        })
    )

    change_list_template = "curation_tracker/publication_changelist.html"

    def get_readonly_fields(self, request, obj=None):
        if obj:
            fields = ["num","id"]
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
            return []


    def display_doi(self, obj):
        if obj.doi:
            return format_html('<a href="https://doi.org/{}">{}</a>', obj.doi, obj.doi)
        else:
            return obj.doi


    def display_PMID(self, obj):
        if obj.PMID:
            return format_html('<a href="https://europepmc.org/abstract/MED/{}">{}</a>', obj.PMID, obj.PMID)
        else:
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
        return '-'

    def display_second_level_curator(self, obj):
        if obj.second_level_curator:
            return obj.second_level_curator.name
        return None


    def display_second_level_curation_status(self, obj):
        if obj.second_level_curation_status:
            return obj.second_level_curation_status
        return '-'


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


    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('import-csv/', self.import_csv),
        ]
        return my_urls + urls


    def import_csv(self, request):
        if request.method == "POST":
            csv_file = request.FILES["csv_file"]
            print(f">> File: {csv_file}")
            file_data = csv_file.read().decode('utf-8')
            cvs_data = file_data.split('\n')
            msg = ''
            for x in cvs_data:
                if x != '':
                    print(f"\n# Data: {x}")
                    if check_publication_exist(x):
                        msg = msg + f"<br/>&#10060; - '{x}' already exists in the database - no import"
                    else:
                        pub_data = {}
                        data = query_epmc(x)
                        if data:
                            pub_data['title'] = data['title']
                            pub_data['doi'] = data['doi']
                            pub_data['year'] = data['firstPublicationDate'].split('-')[0]
                            print(f"> Title: {pub_data['title']}")
                            print(f"> DOI: {pub_data['doi']}")
                            print(f"> Year: {pub_data['year']}")
                            if data['pubType'] == 'preprint':
                                pub_data['journal'] = data['bookOrReportDetails']['publisher']
                            else:
                                pub_data['journal'] = data['journalTitle']
                                pub_data['PMID'] = data['pmid']
                                print(f"> PMID: {data['pmid']}")
                            print(f"> Journal: {pub_data['journal']}")

                        # Create new model in DB
                        model = CurationPublicationAnnotation()
                        model.set_annotation_ids(next_id_number(CurationPublicationAnnotation))
                        setattr(model,'study_name',x)
                        for field in pub_data.keys():
                            setattr(model, field, pub_data[field])
                        model.save(using=tracker_db)

                        if data:
                            msg = msg + f"<br/>&#10004; - '{x}' has been successfully imported in the database"
                        else:
                            msg = msg + f"<br/>&#10004; - '{x}' has been imported in the database but extra information couldn't be extracted from EuropePMC"

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


curation_tracker_site = admin.AdminSite('curation_tracker')
curation_tracker_site.register(CurationCurator, CurationCuratorAdmin)
curation_tracker_site.register(CurationPublicationAnnotation, CurationPublicationAnnotationAdmin)
