import django_tables2 as tables
from django.conf import settings
from django.utils.html import format_html
from .models import *
from django.utils.crypto import get_random_string

relative_path = '../..'
publication_path = relative_path+'/publication'
trait_path = relative_path+'/trait'

def smaller_in_bracket(value):
    bracket_left = '['
    value = value.replace(' '+bracket_left, bracket_left)
    value = value.replace(bracket_left,'<span class="smaller_90 pl-2"><span class="pgs_colour_2">[</span>')
    value = value.replace(']','<span class="pgs_colour_2">]</span></span>')
    return value

class Column_joinlist(tables.Column):
    def render(self, value):
        values = smaller_in_bracket('<br/>'.join(value))
        return format_html(values)

class Column_shorten_text_content(tables.Column):
    def render(self, value):
        return format_html('<span class="more">'+value+'</span>')

class Column_metriclist(tables.Column):
    def render(self, value):
        l = []
        for x in value:
            name, val = x
            if len(name) == 2:
                name_html = format_html('<span title="{}" class="pgs_helptip">{}</span>', name[0], name[1])
            else:
                name_html = format_html('<span title="{}" class="pgs_helptip">{}</span>', name[0], name[0])
            l.append((name_html, '<span class="pgs_nowrap">'+str(val)+'</span>'))

        values = smaller_in_bracket('<br>'.join([': '.join(x) for x in l]))
        return format_html(values)

class Column_demographic(tables.Column):
    def render(self, value):
        l = []

        #Estimate
        e = ''
        if value.estimate != None:
            e += '{} = {}'.format(value.estimate_type.title(), value.estimate)
            if value.range != None and value.range_type.lower() == 'ci':
                e += ' {}'.format(smaller_in_bracket(str(value.range)))
            e += ' {}'.format(value.unit)
        if len(e) > 0:
            l.append(e)

        #Variability
        v = None
        if value.variability != None:
            v = '{} = {} {}'.format(value.variability_type.title(), value.variability, value.unit)
        if v != None:
            l.append(v)

        #Range
        r = None
        if '[' not in e:
            if value.range != None:
                r = '{} = {} {}'.format(value.range_type.title(), smaller_in_bracket(str(value.range)), value.unit)
        if r != None:
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
    def render(self, value):
        citation, pgp, externality = value.split('|')
        if externality == 'E':
            return format_html('<a href="'+publication_path+'/{}">{}</a> <sup class="pgs_sup" title="External PGS evaluation">Ext.</sup>', pgp, format_html(citation))
        else:
            return format_html('<a href="'+publication_path+'/{}">{}</a>', pgp, format_html(citation))

class Column_pubexternality_PGS(tables.Column):
    def render(self, value):
        citation, pgp, externality = value.split('|')
        if externality == 'E':
            return format_html('<a href="'+publication_path+'/{}">{}</a> <sup class="pgs_sup" title="External PGS evaluation">Ext.</sup>', pgp, format_html(citation))
        elif externality == 'D':
            return format_html('<a href="'+publication_path+'/{}">Original Report</a>', pgp)
        else:
            return format_html('<a href="'+publication_path+'/{}">{}</a>', pgp, format_html(citation))

class Column_cohorts(tables.Column):
    def render(self, value):
        qset = value.all()
        qdict = {}
        qlist = []
        for q in qset:
            r = format_html('<span title="{}" data-content="{}" class="pgs_helpover">{}</span>', q.name_short, q.name_full, q.name_short)
            qdict[q.name_short] = r
        for k in sorted (qdict):
            qlist.append(qdict[k])
        if len(qlist) > 5:
            div_id = get_random_string(10)
            html_list = '<a class="toggle_table_btn" id="'+div_id+'" title="Click to expand/collapse the list">'+str(len(qlist))+' cohorts <i class="fa fa-plus-circle"></i></a>'
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
    scores_count = tables.Column(accessor='scores_count', verbose_name='PGS Developed', orderable=False)
    scores_evaluated = tables.Column(accessor='scores_evaluated', verbose_name='PGS Evaluated', orderable=False)

    class Meta:
        model = Publication
        attrs = {
            "data-show-columns" : "true",
            "data-sort-name" : "id",
            "data-page-size" : "50"
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
        return format_html('<i>{}</i>', value)

    def render_doi(self, value):
        return format_html('<a class="pgs_nowrap" href=https://doi.org/{}>{}</a>', value, value)

    def render_PMID(self, value):
        return format_html('<a href="https://www.ncbi.nlm.nih.gov/pubmed/{}">{}</a>', value, value)



class Browse_TraitTable(tables.Table):
    '''Table to browse Traits in the PGS Catalog'''
    label_link = Column_format_html(accessor='display_label', verbose_name='Trait (ontology term label)', orderable=True)
    scores_count = tables.Column(accessor='scores_count', verbose_name='Number of Related PGS')
    id_url = Column_format_html(accessor='display_id_url', verbose_name='Trait Identifier (Experimental Factor Ontology ID)')
    category_labels = tables.Column(accessor='category_labels', verbose_name='Trait Category')

    class Meta:
        model = EFOTrait
        attrs = {
            "data-show-columns" : "true",
            "data-sort-name" : "display_label",
            "data-page-size" : "50"
        }
        fields = [
            'label_link',
            'id_url',
            'category_labels',
            'scores_count'
        ]
        template_name = 'catalog/pgs_catalog_django_table.html'


class Browse_ScoreTable(tables.Table):
    '''Table to browse Scores (PGS) in the PGS Catalog'''
    list_traits = tables.Column(accessor='list_traits', verbose_name='Mapped Trait(s)\n(Ontology)', orderable=False)
    ftp_link = tables.Column(accessor='link_filename', verbose_name=format_html('PGS Scoring File (FTP Link)'), orderable=False)

    relative_path = '../..'

    class Meta:
        model = Score
        attrs = {
            "data-show-columns" : "true",
            "data-sort-name" : "id",
            "data-page-size" : "50"
        }
        fields = [
            'id',
            'name',
            'publication',
            'trait_reported',
            'list_traits',
            'variants_number',
            'ftp_link'
        ]
        template_name = 'catalog/pgs_catalog_django_table.html'

    def render_id(self, value):
        global relative_path
        return format_html('<a href='+relative_path+'/pgs/{}>{}</a>', value, value)

    def render_publication(self, value):
        citation = format_html(' '.join([value.id, '<br/><small><i class="fa fa-angle-double-right"></i>', value.firstauthor, '<i>et al.</i>', value.journal, '(%s)'%value.date_publication.strftime('%Y'), '</small>']))
        return format_html('<a href="'+publication_path+'/{}">{}</a>', value.id, citation)

    def render_list_traits(self, value):
        l = []
        for x in value:
            l.append('<a href=../../trait/{}>{}</a>'.format(x[0], x[1]))
        return format_html('<br>'.join(l))

    def render_ftp_link(self, value):
        id = value.split('.')[0]
        ftp_link = settings.USEFUL_URLS['PGS_FTP_HTTP_ROOT']+'/scores/{}/ScoringFiles/{}'.format(id, value)
        return format_html('<a class="pgs_no_icon_link file_link" href="{}" title="Download PGS Scoring File (variants, weights)" download><i class="fa fa-file-text"></i></a><span class="only_export">{}</span>', ftp_link, ftp_link)

    def render_variants_number(self, value):
        return '{:,}'.format(value)


class Browse_SampleSetTable(tables.Table):
    '''Table to browse SampleSets (PSS; used in PGS evaluations) in the PGS Catalog'''
    sample_merged = Column_sample_merged(accessor='display_samples_for_table', verbose_name='Sample Numbers', orderable=False)
    sample_ancestry = Column_ancestry(accessor='display_ancestry', verbose_name='Sample Ancestry', orderable=False)
    sampleset = tables.Column(accessor='display_sampleset', verbose_name=format_html('PGS Sample Set ID<br />(PSS ID)'), orderable=False)
    phenotyping_free = Column_shorten_text_content(accessor='phenotyping_free', verbose_name='Detailed Phenotype Description')
    cohorts = Column_cohorts(accessor='cohorts', verbose_name='Cohort(s)')

    class Meta:
        model = Sample
        attrs = {
            "data-show-columns" : "true",
            "data-page-size" : "50"
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
         return format_html('<a href="../../sampleset/{}">{}</span>', value, value)

    def render_phenotyping_free(self, value):
        return format_html('<span class="more">{}</span>', value)

    def render_cohorts_additional(self, value):
        return format_html('<span class="more">{}</span>', value)


class SampleTable_variants_details(tables.Table):
    sample_merged = Column_sample_merged(accessor='display_samples_for_table', verbose_name='Sample Numbers', orderable=False)
    sources = Column_joinlist(accessor='display_sources', verbose_name='PubMed ID', orderable=False)
    sample_ancestry = Column_ancestry(accessor='display_ancestry', verbose_name='Sample Ancestry', orderable=False)

    class Meta:
        model = Sample
        attrs = {
            "data-show-columns" : "true",
            "data-sort-name" : "display_ancestry"
        }
        fields = [
            'sources',
            'sample_merged', 'sample_ancestry', 'ancestry_country'
        ]
        template_name = 'catalog/pgs_catalog_django_table.html'


    def render_sources(self, value):
        pmid = ''
        if 'PMID' in value and value['PMID']:
            pmid = '<a href="https://www.ncbi.nlm.nih.gov/pubmed/{}">{}</a>'.format(value['PMID'], value['PMID'])
        return format_html(pmid)


class SampleTable_variants(tables.Table):
    '''Table on PGS page - displays information about the GWAS samples used'''
    sample_merged = Column_sample_merged(accessor='display_samples_for_table', verbose_name='Sample Numbers', orderable=False)
    sources = Column_joinlist(accessor='display_sources', verbose_name='Study Identifiers', orderable=False)
    sample_ancestry = Column_ancestry(accessor='display_ancestry', verbose_name='Sample Ancestry', orderable=False)

    class Meta:
        model = Sample
        attrs = {
            "data-show-columns" : "true"
        }
        fields = [
            'sources',
            'sample_merged', 'sample_ancestry'
        ]
        template_name = 'catalog/pgs_catalog_django_table.html'


    def render_sources(self, value):
        l = []
        if 'GCST' in value:
            l.append('GWAS Catalog: <a href="https://www.ebi.ac.uk/gwas/studies/{}">{}</a>'.format(value['GCST'], value['GCST']))
        if 'PMID' in value and value['PMID']:
            l.append('PubMed: <a href="https://www.ncbi.nlm.nih.gov/pubmed/{}">{}</a>'.format(value['PMID'], value['PMID']))
        return format_html('<br>'.join(l))

    def render_source_GWAS_catalog(self, value):
        if value.startswith('GCST'):
            return format_html('<a href="https://www.ebi.ac.uk/gwas/studies/{}">{}</a>', value, value)
        else:
            return value

    def render_source_PMID(self, value):
        return format_html('<a href="https://www.ncbi.nlm.nih.gov/pubmed/{}">{}</a>', value, value)


class SampleTable_training(tables.Table):
    '''Table on PGS page - displays information about the samples used in Score Development'''
    sample_merged = Column_sample_merged(accessor='display_samples_for_table', verbose_name='Sample Numbers', orderable=False)
    sample_ancestry = Column_ancestry(accessor='display_ancestry', verbose_name='Sample Ancestry', orderable=False)
    cohorts = Column_cohorts(accessor='cohorts', verbose_name='Cohort(s)')

    # Demographics (Column_demographic)
    followup_time = Column_demographic(accessor='followup_time', verbose_name='Participant Follow-up Time', orderable=False)
    sample_age = Column_demographic(accessor='sample_age', verbose_name='Age of Study Participants', orderable=False)

    class Meta:
        model = Sample
        attrs = {
            "data-show-columns" : "true"
        }
        fields = [
            'phenotyping_free',
            'followup_time',
            'sample_merged',
            'sample_age',
            'sample_ancestry','ancestry_additional',
            'cohorts', 'cohorts_additional'
        ]
        template_name = 'catalog/pgs_catalog_django_table.html'

    def render_phenotyping_free(self, value):
        return format_html('<span class="more">{}</span>', value)


class SampleTable_performance(tables.Table):
    '''Table on PGS page - displays information about the samples used in for PGS evaluation (accessed by PSS)'''
    sample_merged = Column_sample_merged(accessor='display_samples_for_table', verbose_name='Sample Numbers', orderable=False)
    sample_ancestry = Column_ancestry(accessor='display_ancestry', verbose_name='Sample Ancestry', orderable=False)
    sampleset = tables.Column(accessor='display_sampleset', verbose_name=format_html('PGS Sample Set ID<br />(PSS ID)'), orderable=False)
    phenotyping_free = tables.Column(accessor='phenotyping_free', verbose_name='Detailed Phenotype Description')
    cohorts = Column_cohorts(accessor='cohorts', verbose_name='Cohort(s)')

    # Demographics (Column_demographic)
    followup_time = Column_demographic(accessor='followup_time', verbose_name='Participant Follow-up Time', orderable=False)
    sample_age = Column_demographic(accessor='sample_age', verbose_name='Age of Study Participants', orderable=False)

    class Meta:
        model = Sample
        attrs = {
            "data-show-columns" : "true",
            "data-sort-name" : "display_sampleset"
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
         return format_html('<a id="{}" href="../../sampleset/{}">{}</span>', value, value, value)

    def render_phenotyping_free(self, value):
        return format_html('<span class="more">{}</span>', value)

    def render_cohorts_additional(self, value):
        return format_html('<span class="more">{}</span>', value)


class PerformanceTable(tables.Table):
    '''On each PGS page - Displays PGS Performance metrics'''
    id = tables.Column(accessor='id', verbose_name=format_html('PGS Performance Metric ID<br />(PPM ID)'))
    sampleset = tables.Column(accessor='sampleset', verbose_name=format_html('PGS Sample Set ID<br />(PSS ID)'))
    trait_info = Column_trait(accessor='display_trait', verbose_name='Trait', orderable=False)
    effect_sizes = Column_metriclist(accessor='effect_sizes_list', verbose_name=format_html('PGS Effect Sizes<br>(per SD change)'), orderable=False)
    class_accuracy = Column_metriclist(accessor='class_acc_list', verbose_name='PGS Classification Metrics', orderable=False)
    othermetrics = Column_metriclist(accessor='othermetrics_list', verbose_name='Other Metrics', orderable=False)
    pub_withexternality = Column_pubexternality(accessor='publication_withexternality', verbose_name='Performance Source', orderable=False)
    covariates = Column_shorten_text_content(accessor='covariates')
    performance_comments = Column_shorten_text_content(accessor='performance_comments')

    class Meta:
        model = Performance
        attrs = {
            "data-show-columns" : "true",
            "data-sort-name" : "id"
        }
        fields = [
            'id', 'sampleset', 'pub_withexternality',
            'trait_info',
            'effect_sizes', 'class_accuracy', 'othermetrics',
            'covariates', 'performance_comments'
        ]
        template_name = 'catalog/pgs_catalog_django_table.html'

    def render_sampleset(self, value):
        return format_html('<a href="#{}">{}</a>', value, value)


class PerformanceTable_PubTrait(tables.Table):
    '''On each Performance/trait page - Displays PGS Performance metrics'''
    id = tables.Column(accessor='id', verbose_name=format_html('PGS Performance Metric ID<br />(PPM ID)'))
    trait_info = Column_trait(accessor='display_trait', verbose_name='Trait', orderable=False)
    sampleset = tables.Column(accessor='sampleset', verbose_name=format_html('PGS Sample Set ID<br/>(PSS ID)'), orderable=False)
    effect_sizes = Column_metriclist(accessor='effect_sizes_list', verbose_name=format_html('PGS Effect Sizes<br/>(per SD change)'), orderable=False)
    class_accuracy = Column_metriclist(accessor='class_acc_list', verbose_name='PGS Classification Metrics', orderable=False)
    othermetrics = Column_metriclist(accessor='othermetrics_list', verbose_name='Other Metrics', orderable=False)
    pub_withexternality = Column_pubexternality(accessor='publication_withexternality', verbose_name='Performance Source',orderable=False)

    class Meta:
        model = Performance
        attrs = {
            "data-show-columns" : "true",
            "data-sort-name" : "id"
        }
        fields = [
            'id','score', 'sampleset', 'pub_withexternality',
            'trait_info',
            'effect_sizes', 'class_accuracy', 'othermetrics',
            'covariates', 'performance_comments'
        ]
        template_name = 'catalog/pgs_catalog_django_table.html'

    def render_sampleset(self, value):
        return format_html('<a href="#{}">{}</a>', value, value)

    def render_score(self, value):
        return format_html('<a href="../../pgs/{}">{}</a> (<i>{}</i>)', value.id, value.id, value.name)


class CohortTable(tables.Table):
    '''Displays information about Cohorts that have been cited by PGS'''

    class Meta:
        attrs = {
            "data-show-columns" : "false",
            "data-sort-name" : "name_short"
        }
        model = Cohort
        fields = [
            'name_short', 'name_full'
        ]
        template_name = 'catalog/pgs_catalog_django_table.html'
