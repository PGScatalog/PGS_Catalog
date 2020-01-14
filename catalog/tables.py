import django_tables2 as tables
from django.utils.html import format_html
from .models import Publication, Sample, SampleSet, Score, Performance, EFOTrait

class Column_joinlist(tables.Column):
    def render(self, value):
        return format_html('<br>'.join(value))

class Column_metriclist(tables.Column):
    def render(self, value):
        l = []
        for x in value:
            name, val = x
            if len(name) == 2:
                name_html = format_html('<span title="{}" style="text-decoration:underline dotted">{}</span>', name[0], name[1])
            else:
                name_html = format_html('<span title="{}" style="text-decoration:underline dotted">{}</span>', name[0], name[0])
            l.append((name_html, val))
        return format_html('<br>'.join([': '.join(x) for x in l]))

class Column_trait(tables.Column):
    def render(self, value):
        l = []
        if 'reported' in value:
            l.append('<u>Reported Trait</u>: {}'.format(value['reported']))
        if 'efo' in value:
            v = []
            for trait in value['efo']:
                v.append(format_html('<a href=../../traits/{}>{}</a>', trait.id, trait.label))
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
            return format_html('<a href=../../publication/{}>{}</a> <sup title="External PGS evaluation"; style="color:rgb(0,124,130)";>Ext.</sup>', pgp, format_html(citation))
        else:
            return format_html('<a href=../../publication/{}>{}</a>', pgp, format_html(citation))

class Column_pubexternality_PGS(tables.Column):
    def render(self, value):
        citation, pgp, externality = value.split('|')
        if externality == 'E':
            return format_html('<a href=../../publication/{}>{}</a> <sup title="External PGS evaluation"; style="color:rgb(0,124,130)";>Ext.</sup>', pgp, format_html(citation))
        elif externality == 'D':
            return format_html('<a href=../../publication/{}>Original Report</a>', pgp)
        else:
            return format_html('<a href=../../publication/{}>{}</a>', pgp, format_html(citation))


class Browse_PublicationTable(tables.Table):
    scores_count = tables.Column(accessor='scores_count', verbose_name='Number of PGS Developed', orderable=False)
    scores_evaluated = tables.Column(accessor='scores_evaluated', verbose_name='Number of PGS Evaluated', orderable=False)

    class Meta:
        model = Publication
        exclude = [
            'authors',
            'num'
        ]
        sequence = ('id', 'scores_count', 'scores_evaluated','firstauthor', 'title', 'journal', 'date_publication', 'doi', 'PMID' )
        attrs = {"tbody": {'id': "filterableTable"}}
        template_name = 'django_tables2/bootstrap.html'

    def render_id(self, value):
        return format_html('<a href=../../publication/{}>{}</a>', value, value)

    def render_journal(self, value):
        return format_html('<i>{}</i>', value)

    def render_doi(self, value):
        return format_html('<a href=https://doi.org/{}>{}</a>', value, value)

    def render_PMID(self, value):
        return format_html('<a href=https://www.ncbi.nlm.nih.gov/pubmed/{}>{}</a>', value, value)



class Browse_TraitTable(tables.Table):
    scores_count = tables.Column(accessor='scores_count', verbose_name='Number of PGS Developed', orderable=False)
    url = tables.Column(accessor='url', verbose_name='Link to Ontology', orderable=False)

    class Meta:
        model = EFOTrait

        exclude = [
            'description'
        ]
        attrs = {"tbody": {'id': "filterableTable"}}
        sequence = ('id', 'label', 'scores_count', 'url')
        template_name = 'django_tables2/bootstrap.html'

    def render_description(self, value):
        value = eval(value)
        return format_html('<br>'.join(value))

    def render_id(self, value):
        return format_html('<a href=../../trait/{}>{}</a>', value, value)

    def render_url(self, value):
        return format_html('<a href={}>EFO <i class="icon icon-common icon-external-link-alt"></i></a>',value)

class Browse_ScoreTable(tables.Table):
    list_traits = tables.Column(accessor='list_traits', verbose_name='Mapped Trait(s)\n(EFO)', orderable=False)
    ftp_link = tables.Column(accessor='link_filename', verbose_name=format_html('PGS Download Links <i class="icon icon-common" data-icon="&#xf019;"></i>'), orderable=False)

    class Meta:
        model = Score
        fields = [
            'id',
            'name',
            'publication',
            'trait_reported',
            'list_traits',
            'variants_number',
            'ftp_link'
        ]
        attrs = {"tbody" : {'id' :"filterableTable"}}
        template_name = 'django_tables2/bootstrap.html'

    def render_id(self, value):
        return format_html('<a href=../../pgs/{}>{}</a>', value, value)

    def render_publication(self, value):
        citation = format_html(' '.join([value.firstauthor, '<i>et al.</i>', value.journal, '(%s)'%value.date_publication.strftime('%Y')]))
        return format_html('<a href=../../publication/{}>{}</a>', value.id, citation)

    def render_list_traits(self, value):
        l = []
        for x in value:
            l.append('<a href=../../trait/{}>{}</a>'.format(x[0], x[1]))
        return format_html('<br>'.join(l))

    def render_ftp_link(self, value):
        return format_html('<a href="ftp://ftp.ebi.ac.uk/pub/databases/spot/pgs/ScoringFiles_formatted/{}" download>FTP Link</a>', value)

    def render_variants_number(self, value):
        return '{:,}'.format(value)

class SampleTable_variants(tables.Table):
    sample_merged = Column_joinlist(accessor='display_samples', verbose_name='Sample Numbers', orderable=False)
    sources = Column_joinlist(accessor='display_sources', verbose_name='Study Identifiers', orderable=False)
    sample_ancestry = Column_ancestry(accessor='display_ancestry', verbose_name='Sample Ancestry', orderable=False)

    class Meta:
        model = Sample
        fields = [
            'sources',
            #'source_GWAS_catalog','source_PMID',
            'sample_merged', 'sample_ancestry'
        ]
        template_name = 'django_tables2/bootstrap.html'


    def render_sources(self, value):
        l = []
        if 'GCST' in value:
            l.append('GWAS Catalog: <a href=https://www.ebi.ac.uk/gwas/studies/{}>{}</a>'.format(value['GCST'], value['GCST']))
        if 'PMID' in value:
            l.append('PubMed: <a href=https://www.ncbi.nlm.nih.gov/pubmed/{}>{}</a>'.format(value['PMID'], value['PMID']))
        return format_html('<br>'.join(l))

    def render_source_GWAS_catalog(self, value):
        if value.startswith('GCST'):
            return format_html('<a href=https://www.ebi.ac.uk/gwas/studies/{}>{}</a>', value, value)
        else:
            return value

    def render_source_PMID(self, value):
        return format_html('<a href=https://www.ncbi.nlm.nih.gov/pubmed/{}>{}</a>', value, value)


class SampleTable_training(tables.Table):
    sample_merged = Column_joinlist(accessor='display_samples', verbose_name='Sample Numbers', orderable=False)
    sample_ancestry = Column_ancestry(accessor='display_ancestry', verbose_name='Sample Ancestry', orderable=False)

    class Meta:
        model = Sample
        fields = [
            'phenotyping_free',
            'sample_merged',
            'sample_ancestry','ancestry_additional',
            'cohorts', 'cohorts_additional'
        ]
        template_name = 'django_tables2/bootstrap.html'

    def render_phenotyping_free(self, value):
        return format_html('<span class="more">{}</span>', value)

    def render_cohorts(self, value):
        qset = value.all()
        qlist = []
        for q in qset:
            r = format_html('<span title="{}" style="text-decoration:underline dotted">{}</span>', q.name_full, q.name_short)
            qlist.append(r)
        qlist.sort()
        return format_html(', '.join(qlist))

class SampleTable_performance(tables.Table):
    sample_merged = Column_joinlist(accessor='display_samples', verbose_name='Sample Numbers', orderable=False)
    sample_ancestry = Column_ancestry(accessor='display_ancestry', verbose_name='Sample Ancestry', orderable=False)
    sampleset = tables.Column(accessor='display_sampleset', verbose_name='PGS Catalog Sample Set (PSS) ID', orderable=False)

    class Meta:
        model = Sample
        fields = [
            'sampleset',
            'phenotyping_free',
            'sample_merged',
            'sample_ancestry','ancestry_additional',
            'cohorts', 'cohorts_additional',
        ]

        row_attrs = {
            "id": lambda record: record.sampleset.all()[0]
        }

        template_name = 'django_tables2/bootstrap.html'

    def render_phenotyping_free(self, value):
        return format_html('<span class="more">{}</span>', value)

    def render_cohorts(self, value):
        qset = value.all()
        qlist = []
        for q in qset:
            r = format_html('<span title="{}" style="text-decoration:underline dotted">{}</span>', q.name_full, q.name_short)
            qlist.append(r)
        qlist.sort()
        return format_html(', '.join(qlist))

    def render_cohorts_additional(self, value):
        return format_html('<span class="more">{}</span>', value)


class PerformanceTable(tables.Table):
    trait_info = Column_trait(accessor='display_trait', verbose_name='Trait', orderable=False)
    effect_sizes = Column_metriclist(accessor='effect_sizes_list', verbose_name=format_html('PGS Effect Sizes<br>(per SD change)'), orderable=False)
    class_accuracy = Column_metriclist(accessor='class_acc_list', verbose_name='PGS Classification Metrics', orderable=False)
    othermetrics = Column_metriclist(accessor='othermetrics_list', verbose_name='Other Metrics', orderable=False)
    pub_withexternality = Column_pubexternality(accessor='publication_withexternality', verbose_name='Performance Source', orderable=False)

    class Meta:
        model = Performance
        fields = [
            'id', 'sampleset', 'pub_withexternality',
            'trait_info',
            'effect_sizes', 'class_accuracy', 'othermetrics',
            'covariates', 'performance_comments'
        ]
        template_name = 'django_tables2/bootstrap.html'

    def render_sampleset(self, value):
        return format_html('<a href="#{}">{}</a>', value, value)

class PerformanceTable_PubTrait(tables.Table):
    trait_info = Column_trait(accessor='display_trait', verbose_name='Trait', orderable=False)
    effect_sizes = Column_metriclist(accessor='effect_sizes_list', verbose_name=format_html('PGS Effect Sizes<br>(per SD change)'), orderable=False)
    class_accuracy = Column_metriclist(accessor='class_acc_list', verbose_name='PGS Classification Metrics', orderable=False)
    othermetrics = Column_metriclist(accessor='othermetrics_list', verbose_name='Other Metrics', orderable=False)
    pub_withexternality = Column_pubexternality(accessor='publication_withexternality', verbose_name='Performance Source',orderable=False)

    class Meta:
        model = Performance
        fields = [
            'id','score', 'sampleset', 'pub_withexternality',
            'trait_info',
            'effect_sizes', 'class_accuracy', 'othermetrics',
            'covariates', 'performance_comments'
        ]
        template_name = 'django_tables2/bootstrap.html'

    def render_sampleset(self, value):
        return format_html('<a href="#{}">{}</a>', value, value)

    def render_score(self, value):
        return format_html('<a href="../../pgs/{}">{}</a> (<i>{}</i>)', value.id, value.id, value.name)
