import re
import django_tables2 as tables
from django.utils.html import format_html
from django.utils.crypto import get_random_string
from django.conf import settings
from pgs_web import constants
from catalog import common
from .models import *


publication_path = '/publication'
trait_path = '/trait'
page_size = "50"
empty_cell_char = '—'
is_pgs_on_curation_site = settings.PGS_ON_CURATION_SITE


def smaller_in_bracket(value):
    bracket_left = '['
    value = value.replace(' '+bracket_left, bracket_left)
    value = value.replace(bracket_left,'<span class="smaller_90 pgs_bracket pl-2"><span class="only_export"> [</span>')
    value = value.replace(']','<span class="only_export">]</span></span>')
    return value


def smaller_in_parenthesis(value):
    parenthesis_left = '('
    value = value.replace(parenthesis_left,'<span class="smaller_90">(')
    value = value.replace(')',')</span>')
    return value


def score_format(value):
    return format_html(f'<a href="/score/{value.id}">{value.id}</a> <div class="small">({value.name})</div>')


def publication_format(value, is_external=False):
    pub_date = value.pub_year
    citation = f'<span class="only_export">|</span><div class="pgs_pub_details">{value.firstauthor} <i>et al.</i> {value.journal} ({pub_date})</div>'
    extra_html = ''
    if is_external:
        extra_html += '<span class="only_export">|</span><span class="badge badge-pgs-small" data-toggle="tooltip" title="External PGS evaluation">Ext.</span>'
    if value.is_preprint:
        extra_html += '<span class="only_export">|</span><span class="badge badge-pgs-small-2 ml-1" data-toggle="tooltip" title="Preprint (manuscript has not undergone peer review)">Pre</span>'
    return format_html(f'<a href="{publication_path}/{value.id}">{value.id}</a> {citation}{extra_html}')


class Column_joinlist(tables.Column):
    def render(self, value):
        values = smaller_in_bracket('<br/>'.join(value))
        return format_html(values)

class Column_shorten_text_content(tables.Column):
    def render(self, value):
        return format_html('<span class="more">{}</span>', value)

class Column_metriclist(tables.Column):
    def render(self, value):
        l = []
        for x in value:
            name, val = x
            helptip_str = ''
            if len(name) == 2:
                label = name[1]
            else:
                label = name[0]
            if label != name[0]:
                helptip_str = f' title="{name[0]}" class="pgs_helptip"'
            label = smaller_in_bracket(label)
            label = smaller_in_parenthesis(label)
            name_html = f'<span{helptip_str}>{label}</span>'
            l.append((name_html, '<span class="pgs_nowrap">'+smaller_in_bracket(str(val))+'</span>'))

        values = '<br>'.join([': '.join(x) for x in l])
        return format_html(values)

class Column_demographic(tables.Column):
    def render(self, value):
        l = []

        # Estimate
        e = ''
        if value.estimate != None:
            e = '{} = {} {}'.format(value.estimate_type.title(), value.estimate, value.unit)
            l.append(e)

        # Variability
        if value.variability != None:
            v = '{} = {} {}'.format(value.variability_type.title(), value.variability, value.unit)
            l.append(v)

        # Range
        if '[' not in e and value.range != None:
            range_type = value.range_type
            if value.range_type != 'IQR':
                range_type = range_type.title()
            r = '{} ={} {}'.format(range_type, smaller_in_bracket(str(value.range)), value.unit)
            l.append(r)

        return format_html('<br>'.join(l))

class Column_sample_merged(tables.Column):
    def render(self, value):
        return format_html(value)

class Column_trait(tables.Column):
    def render(self, value):
        l = []
        if 'reported' in value:
            l.append('<u>Reported Trait</u>: {}'.format(value['reported']))
        if 'efo' in value:
            v = []
            for trait in value['efo']:
                v.append(format_html('<a href="'+trait_path+'/{}">{}</a>', trait.id, trait.label))
            l.append('<u>Mapped Trait(s)</u>: {}'.format(', '.join(v)))
        if 'free' in value:
            l.append('<u>Description:</u> {}'.format(value['free']))
        return format_html('<br>'.join(l))

class Column_ancestry(tables.Column):
    def render(self, value):
        return format_html(value)

class Column_pubexternality(tables.Column):
    def render(self, value, record):
        is_ext = False
        if value == 'E':
            is_ext = True
        return publication_format(record.publication, is_ext)

class Column_cohorts(tables.Column):
    def render(self, value):
        qdict = {}
        qlist = []
        for q in value.all():
            r = format_html('<span title="{}" data-content="{}" class="pgs_helpover">{}</span>', q.name_short, q.name_full, q.name_short)
            qdict[q.name_short] = r
        for k in sorted (qdict):
            qlist.append(qdict[k])

        if len(qlist) == 0:
            return 'NR'
        elif len(qlist) > 5:
            div_id = get_random_string(10)
            html_list = '<a class="toggle_table_btn pgs_btn_plus" id="'+div_id+'" title="Click to expand/collapse the list">'+str(len(qlist))+' cohorts</a>'
            html_list = html_list+'<div class="toggle_list" id="list_'+div_id+'">'
            html_list = html_list+"<ul><li>"+'</li><li><span class="only_export">,</span>'.join(qlist)+'</li></ul></div>'
            return format_html(html_list)
        else:
            return format_html(', '.join(qlist))

class Column_format_html(tables.Column):
    def render(self, value):
        return format_html(value)


class Browse_PublicationTable(tables.Table):
    '''Table to browse Publications in the PGS Catalog'''
    id = tables.Column(accessor='id', verbose_name=format_html('PGS Publication/Study ID <span>(PGP)</span>'))
    scores_count = tables.Column(accessor='scores_count', verbose_name='PGS Developed', orderable=False)
    scores_evaluated = tables.Column(accessor='scores_evaluated_count', verbose_name='PGS Evaluated', orderable=False)
    doi = tables.Column(accessor='doi', verbose_name=format_html('Digital object identifier <span>(doi)</span>'))
    PMID = tables.Column(accessor='PMID', verbose_name=format_html('PubMed ID <span>(PMID)</span>'))

    class Meta:
        model = Publication
        attrs = {
            "data-show-columns" : "true",
            "data-sort-name" : "id",
            "data-page-size" : page_size,
            "data-export-options" : '{"fileName": "pgs_publications_data"}'
        }
        fields  = [
            'id',
            'scores_count',
            'scores_evaluated',
            'firstauthor',
            'title',
            'journal',
            'date_publication',
            'doi',
            'PMID'
        ]
        template_name = 'catalog/pgs_catalog_django_table.html'

    def render_id(self, value):
        return format_html('<a href="'+publication_path+'/{}">{}</a>', value, value)

    def render_journal(self, value):
        is_preprint = ''
        for pp_journal in ['bioRxiv','medRxiv','Research Square']:
            if pp_journal in value:
                is_preprint = format_html('<span class="badge badge-pgs-small-2 ml-1" data-toggle="tooltip" title="Preprint (manuscript has not undergone peer review)">Pre</span>')
        return format_html('<i>{}</i>{}', value, is_preprint)

    def render_doi(self, value):
        return format_html('<a class="pgs_nowrap" href="https://doi.org/{}">{}</a>', value, value)

    def render_PMID(self, value):
        return format_html('<a href="https://www.ncbi.nlm.nih.gov/pubmed/{}">{}</a>', value, value)

    def render_date_publication(self,value):
        return value.strftime('%d/%m/%Y')


class Browse_PendingPublicationTable(Browse_PublicationTable):
    # Make some headers shorter
    id = tables.Column(accessor='id', verbose_name='PGS Publication ID', orderable=True)
    journal = tables.Column(accessor='journal', verbose_name='Journal', orderable=True)
    PMID = tables.Column(accessor='PMID', verbose_name='PubMed ID', orderable=True)

    class Meta:
        model = Publication
        attrs = {
            "data-show-columns" : "true",
            "data-sort-name" : "id",
            "data-page-size" : page_size,
            "data-export-options" : '{"fileName": "pgs_pending_publications_data"}'
        }
        fields  = [
            'id',
            'scores_count',
            'scores_evaluated',
            'firstauthor',
            'title',
            'journal',
            'date_publication',
            'doi',
            'PMID',
            'curation_status'
        ]
        template_name = 'catalog/pgs_catalog_django_table.html'


class Browse_TraitTable(tables.Table):
    '''Table to browse Traits in the PGS Catalog'''
    label_link = Column_format_html(accessor='display_label', verbose_name=format_html('Trait <span>(ontology term label)</span>'), orderable=True)
    display_ext_url = Column_format_html(accessor='display_ext_url', verbose_name=format_html('Trait Identifier <span>(ontology ID)</span>'))
    category_labels = Column_format_html(accessor='display_category_labels', verbose_name='Trait Category')
    scores_count = tables.Column(accessor='scores_count', verbose_name='Number of Related PGS')

    class Meta:
        model = EFOTrait
        attrs = {
            "data-show-columns" : "true",
            "data-sort-name" : "display_label",
            "data-page-size" : page_size,
            "data-export-options" : '{"fileName": "pgs_traits_data"}'
        }
        fields = [
            'label_link',
            'display_ext_url',
            'category_labels',
            'scores_count'
        ]
        template_name = 'catalog/pgs_catalog_django_table.html'

    def render_display_ext_url(self, value, record):
        return format_html(f'{value}<span class="only_export">: {record.url}</span>')


class Browse_ScoreTable(tables.Table):
    '''Table to browse Scores (PGS) in the PGS Catalog'''
    id = tables.Column(accessor='id', verbose_name='Polygenic Score ID & Name', orderable=True)
    publication = tables.Column(accessor='publication', verbose_name=format_html('PGS Publication ID <span>(PGP)</span>'), orderable=True)
    trait_efo = tables.Column(accessor='trait_efo', verbose_name=format_html('Mapped Trait(s) <span>(Ontology)</span>'), orderable=False)
    ftp_link = tables.Column(accessor='link_filename', verbose_name=format_html('Scoring File <span>(FTP Link)</span>'), orderable=False)
    ancestries =  Column_format_html(accessor='ancestries', verbose_name='Ancestry distribution', orderable=False)

    class Meta:
        model = Score
        attrs = {
            "id": "scores_table",
            "data-show-columns" : "true",
            "data-sort-name" : "id",
            "data-page-size" : page_size,
            "data-export-options" : '{"fileName": "pgs_scores_data"}'
        }
        fields = [
            'id',
            'publication',
            'trait_reported',
            'trait_efo',
            'variants_number',
            'ancestries',
            'ftp_link'
        ]
        template_name = 'catalog/pgs_catalog_django_table.html'

    def render_id(self, value, record):
        return score_format(record)

    def render_publication(self, value):
        return publication_format(value)

    def render_trait_efo(self,value):
        traits_list = [ t.display_label for t in value.all() ]
        return format_html(',<br />'.join(traits_list))

    def render_ftp_link(self, value, record):
        id = value.split('.')[0]
        ftp_file_link = '{}/scores/{}/ScoringFiles/{}'.format(constants.USEFUL_URLS['PGS_FTP_HTTP_ROOT'], id, value)
        margin_right = ''
        license_icon = ''
        if record.has_default_license == False:
            margin_right = ' mr2'
            license_icon = f'<span class="pgs-info-icon pgs_helpover" title="Terms and Licenses" data-content="{record.license}" data-placement="left"> <span class="only_export"> - Check </span>Terms/Licenses</span>'
        return format_html(f'<span class="file_link{margin_right}" data-toggle="tooltip" data-placement="left"></span> <span class="only_export">{ftp_file_link}</span>{license_icon}')


    def render_variants_number(self, value):
        return '{:,}'.format(value)


    def render_ancestries(self, value, record):
        if not value:
            return '-'

        anc_labels = constants.ANCESTRY_LABELS
        stages = constants.PGS_STAGES

        ancestries_data = value
        pgs_id = record.num
        chart_id = f'ac_{pgs_id}'
        data_stage = {}
        data_title = {}
        anc_list = {}
        multi_list = {}
        anc_all_list = {
            'dev_all': set(),
            'all': set()
        }

        # Fetch the data for each stage
        for stage in stages:
            if stage in ancestries_data:
                ancestries_data_stage = ancestries_data[stage]
                anc_list[stage] = set()
                # Details of the multi ancestry data
                multi_title = {}
                multi_anc = 'multi'
                if multi_anc in ancestries_data_stage:
                    for mt in ancestries_data_stage[multi_anc]:
                        (ma,anc) = mt.split('_')
                        if ma not in multi_title:
                            multi_title[ma] = []
                        multi_title[ma].append(f'<li>{anc_labels[anc]}</li>')

                        if anc == 'MAE':
                            continue
                        # Add to the unique list of ancestries
                        anc_list[stage].add(anc)
                        # Add to the unique list of ALL ancestries
                        anc_all_list['all'].add(anc)
                        # Add to the unique list of DEV ancestries
                        if stage != 'eval':
                            anc_all_list['dev_all'].add(anc)

                # Ancestry data for the stage: distribution, list of ancestries and content of the chart tootlip
                data_stage[stage] = []
                data_title[stage] = []
                for key,val in sorted(ancestries_data_stage['dist'].items(), key=lambda item: float(item[1]), reverse=True):
                    label = anc_labels[key]
                    data_stage[stage].append(f'"{key}",{val}')
                    extra_title = ''
                    if key in multi_title:
                        extra_title += '<ul>'+''.join(multi_title[key])+'</ul>'
                    data_title[stage].append(f'<div class=\'{key}\'>{val}%{extra_title}</div>')

                    if key == 'MAE':
                        continue
                    # Add to the unique list of ancestries
                    anc_list[stage].add(key)
                    # Add to the unique list of ALL ancestries
                    anc_all_list['all'].add(key)
                    # Add to the unique list of DEV ancestries
                    if stage != 'eval':
                        anc_all_list['dev_all'].add(key)


        # Skip if no expected data "stage" available
        if data_stage.keys() == 0:
            return None

        # Format the data for each stage: build the HTML
        html_list = []
        html_filter = []
        for stage in stages:
            if stage in data_stage:
                id = chart_id+'_'+stage
                anc_list_stage = anc_list[stage]

                if len(anc_list_stage) > 1:
                    anc_list_stage.add('MAO')
                if 'EUR' not in anc_list_stage:
                    anc_list_stage.add('non-EUR')

                anc_list_stage = [f'"{x}"' for x in list(anc_list_stage)]

                html_filter.append("data-anc-"+stage+"='["+','.join(anc_list_stage)+"]'")

                title_count = ''
                count = ancestries_data[stage]['count']
                if count != 0:
                    title_count = '<span>{:,}</span>'.format(count)
                title = ''.join(data_title[stage])+title_count
                html_chart = f'<div class="anc_chart" data-toggle="tooltip" title="'+title+'" data-id="'+id+'" data-type="'+stage+'" data-chart=\'[['+'],['.join(data_stage[stage])+']]\'><svg id="'+id+'"></svg></div>'
                html_list.append(html_chart)
            else:
                html_list.append('<div>-</div>')


        # All dev and all data
        for all_stages in anc_all_list.keys():
            if len(anc_all_list[all_stages]):
                anc_all_data = anc_all_list[all_stages]

                if len(anc_all_data) > 1:
                    anc_all_data.add('MAO')
                if 'EUR' not in anc_all_data:
                    anc_all_data.add('non-EUR')

                anc_all_data = [f'"{x}"' for x in list(anc_all_data)]

                html_filter.append("data-anc-"+all_stages+"='["+','.join(anc_all_data)+"]'")

        # Wrap up the HTML
        html = '<div class="anc_chart_container" '+' '.join(html_filter)+'>'
        html += ''.join(html_list)
        html += '</div>'
        return format_html(html)


class Browse_ScoreTableEval(Browse_ScoreTable):
    class Meta:
        attrs = {
            "id": "scores_eval_table"
        }
        template_name = 'catalog/pgs_catalog_django_table.html'

class Browse_ScoreTableExample(Browse_ScoreTable):
    class Meta:
        attrs = {
            "id": "scores_eg_table",
            "data-show-columns" : "false",
            "data-show-export" : "false",
            "data-pagination" : "false",
            "data-show-fullscreen" : "false",
            "data-search" : "false"
        }
        template_name = 'catalog/pgs_catalog_django_table.html'


class Browse_SampleSetTable(tables.Table):
    '''Table to browse SampleSets (PSS; used in PGS evaluations) in the PGS Catalog'''
    sample_merged = Column_sample_merged(accessor='display_samples_for_table', verbose_name='Sample Numbers', orderable=False)
    sample_ancestry = Column_ancestry(accessor='display_ancestry', verbose_name='Sample Ancestry', orderable=False)
    sampleset = tables.Column(accessor='display_sampleset', verbose_name=format_html('PGS Sample Set ID<br /><span>(PSS)</span>'), orderable=False)
    phenotyping_free = Column_shorten_text_content(accessor='phenotyping_free', verbose_name='Phenotype Definitions and Methods')
    cohorts = Column_cohorts(accessor='cohorts', verbose_name='Cohort(s)')

    class Meta:
        model = Sample
        attrs = {
            "id": "sampleset_table",
            "data-show-columns" : "true",
            "data-page-size" : page_size,
            "data-export-options" : '{"fileName": "pgs_samplesets_data"}'
        }
        fields = [
            'sampleset',
            'phenotyping_free',
            'sample_merged',
            'sample_ancestry','ancestry_additional',
            'cohorts', 'cohorts_additional',
        ]

        template_name = 'catalog/pgs_catalog_django_table.html'

    def render_sampleset(self, value):
        sampleset = f'<a href="/sampleset/{value.id}">{value.id}</a>'
        if is_pgs_on_curation_site == 'True' and value.name:
            sampleset += f' <div class="small">({value.name})</div>'
        return format_html(sampleset)

    def render_cohorts_additional(self, value):
        return format_html('<span class="more">{}</span>', value)


class SampleTable_variants(tables.Table):
    '''Table on PGS page - displays information about the GWAS samples used'''
    sample_merged = Column_sample_merged(accessor='display_samples_for_table', verbose_name='Sample Numbers', orderable=False)
    sources = Column_joinlist(accessor='display_sources', verbose_name='Study Identifiers', orderable=False)
    sample_ancestry = Column_ancestry(accessor='display_ancestry', verbose_name='Sample Ancestry', orderable=False)
    cohorts = Column_cohorts(accessor='cohorts', verbose_name='Cohort(s)')

    class Meta:
        model = Sample
        attrs = {
            "data-show-columns" : "false",
            "data-sort-name" : "display_sources",
            "data-export-options" : '{"fileName": "pgs_sample_source_data"}'
        }
        fields = [
            'sources',
            'sample_merged', 'sample_ancestry',
            'cohorts'
        ]
        template_name = 'catalog/pgs_catalog_django_table.html'


    def render_sources(self, value):
        l = []
        url = ""
        # GWAS Study ID
        if 'GCST' in value:
            l.append('<div class="gwas_source"><span>GWAS Catalog: <a href="{}/gwas/studies/{}">{}</a></span></div>'.format(constants.USEFUL_URLS['EBI_URL'],value['GCST'], value['GCST']))

        # PubMed ID
        if 'PMID' in value:
            publication_id = value['PMID']
            # PubMed ID
            if re.match(r'^\d+$', str(publication_id)):
                url = "https://europepmc.org/article/MED/{}".format(publication_id)
                l.append('<div>Europe PMC: <a href="{}">{}</a></div>'.format(url, publication_id))
        # DOI or other
        elif 'DOI' in value:
            doi = value['DOI']
            if re.match(r'^10\.',doi):
                publication_id = "DOI:"+doi
                url = "https://europepmc.org/search?query={}".format(publication_id)
                l.append('<div>Europe PMC: <a href="{}">{}</a></div>'.format(url, doi))
            elif re.match(r'^http',doi):
                l.append('<div><a href="{}">{}</a></div>'.format(doi, doi))
            else:
                l.append(f'<div>{doi}</div>')

        if len(l) == 0:
            return empty_cell_char
        else:
            return format_html(''.join(l))


class SampleTable_training(SampleTable_variants):
    '''Table on PGS page - displays information about the samples used in Score Development/Training'''
    phenotyping_free = Column_shorten_text_content(accessor='phenotyping_free', verbose_name='Phenotype Definitions & Methods')

    # Demographics (Column_demographic)
    followup_time = Column_demographic(accessor='followup_time', verbose_name='Participant Follow-up Time', orderable=False)
    sample_age = Column_demographic(accessor='sample_age', verbose_name='Age of Study Participants', orderable=False)

    class Meta:
        model = Sample
        attrs = {
            "data-show-columns" : "true",
            "data-export-options" : '{"fileName": "pgs_sample_development_data"}'
        }
        fields = [
            'sources',
            'sample_merged',
            'sample_ancestry',
            'cohorts',
            'phenotyping_free',
            'sample_age',
            'followup_time',
            'ancestry_additional',
            'cohorts_additional'
        ]
        template_name = 'catalog/pgs_catalog_django_table.html'


class SampleTable_performance(tables.Table):
    '''Table on PGS page - displays information about the samples used in for PGS evaluation (accessed by PSS)'''
    sample_merged = Column_sample_merged(accessor='display_samples_for_table', verbose_name='Sample Numbers', orderable=False)
    sample_ancestry = Column_ancestry(accessor='display_ancestry', verbose_name='Sample Ancestry', orderable=False)
    sampleset = tables.Column(accessor='display_sampleset', verbose_name=format_html('PGS Sample Set ID<br /><span>(PSS)</span>'), orderable=False)
    phenotyping_free = tables.Column(accessor='phenotyping_free', verbose_name='Phenotype Definitions and Methods')
    cohorts = Column_cohorts(accessor='cohorts', verbose_name='Cohort(s)')

    # Demographics (Column_demographic)
    followup_time = Column_demographic(accessor='followup_time', verbose_name='Participant Follow-up Time', orderable=False)
    sample_age = Column_demographic(accessor='sample_age', verbose_name='Age of Study Participants', orderable=False)

    class Meta:
        model = Sample
        attrs = {
            "id": "samples_table",
            "data-show-columns" : "true",
            "data-show-toggle" : "true",
            "data-sort-name" : "display_sampleset",
            "data-export-options" : '{"fileName": "pgs_sample_evaluation_data"}'
        }
        fields = [
            'sampleset',
            'phenotyping_free',
            'followup_time',
            'sample_merged',
            'sample_age',
            'sample_ancestry','ancestry_additional',
            'cohorts', 'cohorts_additional',
        ]

        template_name = 'catalog/pgs_catalog_django_table.html'

    def render_sampleset(self, value):
        sampleset = f'<a id="{value.id}" href="/sampleset/{value.id}">{value.id}</a>'
        if is_pgs_on_curation_site == 'True' and value.name:
            sampleset += f' <div class="small">({value.name})</div>'
        return format_html(sampleset)

    def render_phenotyping_free(self, value):
        return format_html('<span class="more">{}</span>', value)

    def render_cohorts_additional(self, value):
        return format_html('<span class="more">{}</span>', value)


class PerformanceTable(tables.Table):
    '''Displays PGS Performance metrics'''
    id = tables.Column(accessor='id', verbose_name=format_html('PGS Performance<br />Metric ID <span>(PPM)</span>'))
    sampleset = tables.Column(accessor='sampleset', verbose_name=format_html('PGS Sample Set ID<br /><span>(PSS)</span>'))
    trait_info = Column_trait(accessor='display_trait', verbose_name='Trait', orderable=False)
    effect_sizes = Column_metriclist(accessor='effect_sizes_list', verbose_name=format_html('PGS Effect Sizes<br /><span>(per SD change)</span>'), orderable=False)
    class_accuracy = Column_metriclist(accessor='class_acc_list', verbose_name='Classification Metrics', orderable=False)
    othermetrics = Column_metriclist(accessor='othermetrics_list', verbose_name='Other Metrics', orderable=False)
    pub_withexternality = Column_pubexternality(accessor='publication_withexternality', verbose_name='Performance Source', orderable=False)
    covariates = Column_shorten_text_content(accessor='covariates')
    performance_comments = tables.Column(accessor='performance_comments', verbose_name=format_html('PGS Performance:<br />Other Relevant Information'))

    class Meta:
        model = Performance
        attrs = {
            "id": "performances_table",
            "data-show-columns" : "true",
            "data-show-toggle" : "true",
            "data-sort-name" : "id",
            "data-export-options" : '{"fileName": "pgs_performance_metrics_data"}'
        }
        fields = [
            'id', 'score', 'sampleset', 'pub_withexternality',
            'trait_info',
            'effect_sizes', 'class_accuracy', 'othermetrics',
            'covariates', 'performance_comments'
        ]
        template_name = 'catalog/pgs_catalog_django_table.html'

    def render_sampleset(self, value):
        ancestry_key = value.samples_combined_ancestry_key
        ancestry = constants.ANCESTRY_GROUP_LABELS[ancestry_key]
        count_ind = common.individuals_format(value.count_individuals,True)
        sampleset_name = ''
        if is_pgs_on_curation_site == 'True' and value.name:
            sampleset_name = format_html(f'<div>({value.name})</div>')
        return format_html('<a href="#{}">{}</a><span class="only_export">|</span><div class="small">{}<span class="anc_colour_{} mr-1"></span>{}<span class="only_export">|</span>{}</div>', value, value, sampleset_name, ancestry_key, ancestry, count_ind)

    def render_score(self, value):
        return score_format(value)

    def render_performance_comments(self, value):
        comments = value
        has_link = 0
        matches = re.findall('\[([^\]]+)\]\(([^\)]+)\)',value)
        for match in matches:
            has_link = 1
            label = match[0]
            url = match[1]
            html = f'<a href="{url}">{label}</a>'
            comments = comments.replace(f'[{label}]({url})', html)
        if not has_link:
            comments = f'<span class="more">{comments}</span>'
        return format_html(comments)


class CohortTable(tables.Table):
    '''Displays information about Cohorts that have been cited by PGS'''

    class Meta:
        attrs = {
            "data-show-columns" : "false",
            "data-sort-name" : "name_short",
            "data-export-options" : '{"fileName": "pgs_sample_cohorts_data"}'
        }
        model = Cohort
        fields = [
            'name_short', 'name_full', 'name_others'
        ]
        template_name = 'catalog/pgs_catalog_django_table.html'


class EmbargoedScoreTable(tables.Table):
    ''' Displays information about Embargoed Scores '''

    class Meta:
        model = EmbargoedScore
        attrs = {
            "data-show-columns" : "false",
            "data-sort-name" : "id",
            "data-page-size" : page_size,
            "data-export-options" : '{"fileName": "pgs_embargoedscores_data"}'
        }
        fields = [
            'id',
            'name',
            'trait_reported'
        ]
        template_name = 'catalog/pgs_catalog_django_table.html'

    def render_id(self, value):
        return format_html(f'<a href="/score/{value}">{value}</a>')
