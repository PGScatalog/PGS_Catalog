import django_tables2 as tables
from django.utils.html import format_html
from .models import *

page_size = "50"

curation_admin_path = '/admin/curation_tracker'
curation_annotation_path = curation_admin_path+'/curationpublicationannotation'
curation_publication_path = curation_admin_path+'/curationpublication'


# class Column_id_with_link(tables.Column):
#     def render(self, value, record):
#         return format_html('<a href="'+curation_annotation_path+'/{}/change/">{}</a>', record.num, value)


class Column_curation_ids(tables.Column):
    def render(self, value, record):
        html = f'<a href="{curation_annotation_path}/{record.num}/change/" title="Curation Tracker ID">{value}</a>'
        html = html + f'<div class="small mt-1" title="Study name"><span class="pgs_color_1">&rarr;</span> {record.study_name}</div>'
        return format_html(html)


class Column_publication_ids(tables.Column):
    def render(self, value, record):
        html = None
        pmid = record.PMID
        doi = record.doi
        if pmid:
            html = f'<div>PubMed ID: <a href="https://europepmc.org/abstract/MED/{pmid}">{pmid}</a></div>'
        if doi:
            if not html:
                html = ''
            html = html + f'<div>doi: <a href="https://doi.org/{doi}">{doi}</a></div>'
        return format_html(html)


class Column_l1_curation_ids(tables.Column):
    def render(self, value, record):
        curator = '-'
        if record.first_level_curator:
            curator = record.first_level_curator.name
        status = record.first_level_curation_status
        date = record.first_level_date
        html = f'<div><u>Curator:</u> {curator}</div><div><u>Status:</u> {status}</div>'
        if date:
            html = html + f'<div><u>Date:</u> {date}</div>'
        return format_html(html)


class Column_l2_curation_ids(tables.Column):
    def render(self, value, record):
        curator = '-'
        if record.second_level_curator:
            curator = record.second_level_curator.name
        status = record.second_level_curation_status
        date = record.second_level_date
        html = f'<div><u>Curator:</u> {curator}</div><div><u>Status:</u> {status}</div>'
        if date:
            html = html + f'<div><u>Date:</u> {date}</div>'
        return format_html(html)


class Browse_CurationPublicationAnnotationL1(tables.Table):
    id = Column_curation_ids(accessor='id', verbose_name='PGS Literature Triage ID (PGL)', orderable=True)
    publication_ids = Column_publication_ids(accessor='PMID', verbose_name=format_html('Publication IDs'), orderable=False)
    first_level_curator = tables.Column(accessor='first_level_curator', verbose_name=format_html('<span class="pgs_bg_color_amber pl-1 pr-1"><b>L1</b></span> Curator Name'))
    first_level_curation_status = tables.Column(accessor='first_level_curation_status', verbose_name=format_html('<span class="pgs_bg_color_amber pl-1 pr-1"><b>L1</b></span> Curation Status'))
    first_level_comment = tables.Column(accessor='first_level_comment', verbose_name=format_html('<span class="pgs_bg_color_amber pl-1 pr-1"><b>L1</b></span> Curation Comment'))
    eligibility = tables.BooleanColumn(accessor='eligibility', verbose_name='Eligibility')
    embargoed = tables.BooleanColumn(accessor='embargoed', verbose_name='Embargoed')

    class Meta:
        model = CurationPublicationAnnotation
        attrs = {
            "data-show-columns" : "true",
            "data-sort-name" : "id",
            "data-page-size" : page_size,
            "data-export-options" : '{"fileName": "pgs_curation_publication_annotation_l1_data"}'
        }
        fields  = [
            'id',
            # 'study_name',
            'publication_ids',
            'first_level_curator',
            'first_level_curation_status',
            'first_level_comment',
            'eligibility',
            # 'reported_trait',
            # 'gwas_and_pgs',
            'embargoed',
            'comment'
        ]
        template_name = 'catalog/pgs_catalog_django_table.html'


class Browse_CurationPublicationAnnotationL2(tables.Table):
    id = Column_curation_ids(accessor='id', verbose_name=format_html('PGS Literature Triage ID <span>(PGL)</span>'), orderable=True)
    publication_ids = Column_publication_ids(accessor='PMID', verbose_name='Publication IDs', orderable=False)
    l1_curation_status =  Column_l1_curation_ids(accessor='first_level_curation_status', verbose_name=format_html('<span class="pgs_bg_color_amber pl-1 pr-1"><b>L1</b></span> Curation'), orderable=False)
    first_level_comment = tables.Column(accessor='first_level_comment', verbose_name=format_html('<span class="pgs_bg_color_amber pl-1 pr-1"><b>L1</b></span> Curation Comment'))
    second_level_curator = tables.Column(accessor='second_level_curator', verbose_name=format_html('<span class="pgs_bg_color_1 pl-1 pr-1"><b>L2</b></span> Curator Name'))
    second_level_curation_status = tables.Column(accessor='second_level_curation_status', verbose_name=format_html('<span class="pgs_bg_color_1 pl-1 pr-1"><b>L2</b></span> Curation Status'))
    second_level_comment = tables.Column(accessor='second_level_comment', verbose_name=format_html('<span class="pgs_bg_color_1 pl-1 pr-1"><b>L2</b></span> Curation Comment'))
    eligibility = tables.BooleanColumn(accessor='eligibility', verbose_name='Eligibility')
    embargoed = tables.BooleanColumn(accessor='embargoed', verbose_name='Embargoed')

    class Meta:
        model = CurationPublicationAnnotation
        attrs = {
            "data-show-columns" : "true",
            "data-sort-name" : "id",
            "data-page-size" : page_size,
            "data-export-options" : '{"fileName": "pgs_curation_publication_annotation_l2_data"}'
        }
        fields  = [
            'id',
            # 'study_name',
            'publication_ids',
            'l1_curation_status',
            # 'first_level_curator',
            # 'first_level_curation_status',
            # 'first_level_date',
            'first_level_comment',
            'second_level_curator',
            'second_level_curation_status',
            'second_level_comment',
            # 'eligibility',
            # 'reported_trait',
            # 'gwas_and_pgs',
            'embargoed',
            'comment'
        ]
        template_name = 'catalog/pgs_catalog_django_table.html'


class Browse_CurationPublicationAnnotationReleaseReady(tables.Table):
    id = Column_curation_ids(accessor='id', verbose_name='PGS Literature Triage ID (PGL)', orderable=True)
    publication_ids = Column_publication_ids(accessor='PMID', verbose_name=format_html('Publication IDs'), orderable=False)
    l1_curation_status =  Column_l1_curation_ids(accessor='first_level_curation_status', verbose_name=format_html('<span class="pgs_bg_color_amber pl-1 pr-1"><b>L1</b></span> Curation'), orderable=False)
    first_level_comment = tables.Column(accessor='first_level_comment', verbose_name=format_html('<span class="pgs_bg_color_amber pl-1 pr-1"><b>L1</b></span> Curation Comment'))
    l2_curation_status =  Column_l1_curation_ids(accessor='second_level_curation_status', verbose_name=format_html('<span class="pgs_bg_color_1 pl-1 pr-1"><b>L2</b></span> Curation'), orderable=False)
    second_level_comment = tables.Column(accessor='second_level_comment', verbose_name=format_html('<span class="pgs_bg_color_1 pl-1 pr-1"><b>L2</b></span> Curation Comment'))
    eligibility = tables.BooleanColumn(accessor='eligibility', verbose_name='Eligibility')
    embargoed = tables.BooleanColumn(accessor='embargoed', verbose_name='Embargoed')

    class Meta:
        model = CurationPublicationAnnotation
        attrs = {
            "data-show-columns" : "true",
            "data-sort-name" : "id",
            "data-page-size" : page_size,
            "data-export-options" : '{"fileName": "pgs_curation_publication_annotation_to_release_data"}'
        }
        fields  = [
            'id',
            # 'study_name',
            'publication_ids',
            'l1_curation_status',
            # 'first_level_curator',
            # 'first_level_curation_status',
            # 'first_level_date',
            'first_level_comment',
            'l2_curation_status',
            # 'second_level_curator',
            # 'second_level_curation_status',
            # 'second_level_date',
            'second_level_comment',
            'eligibility',
            'reported_trait',
            'gwas_and_pgs',
            'embargoed',
            'comment'
        ]
        template_name = 'catalog/pgs_catalog_django_table.html'
