from django.db import models
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.postgres.fields import DecimalRangeField

class Publication(models.Model):
    """Class for publications with PGS"""
    # Stable identifiers
    num = models.IntegerField('PGS Publication/Study (PGP) Number', primary_key=True)
    id = models.CharField('PGS Publication/Study (PGP) ID', max_length=30, db_index=True)

    date_released = models.DateField('PGS Release Date', null=True, db_index=True)

    # Key information (also) in the spreadsheet
    doi = models.CharField('digital object identifier (doi)', max_length=100)
    PMID = models.IntegerField('PubMed ID (PMID)', null=True)
    journal = models.CharField('Journal Name', max_length=100)
    firstauthor = models.CharField('First Author', max_length=50)

    # Information extracted from EuropePMC
    authors = models.TextField('Authors')
    title = models.TextField('Title')
    date_publication = models.DateField('Publication Date')

    # Curation information
    CURATION_STATUS_CHOICES = [
        ('C',  'Curated'),
        ('ID', 'Curated - insufficient data'),
        ('IP', 'Curation in Progress'),
        ('AW', 'Awaiting Curation')
    ]
    curation_status = models.CharField(max_length=2,
                            choices=CURATION_STATUS_CHOICES,
                            default='AW',
                            verbose_name='Curation Status'
                            )
    curation_notes = models.TextField('Curation Notes', default='')

    # Methods
    def __str__(self):
        return ' | '.join([self.id, self.firstauthor])

    class Meta:
        get_latest_by = 'num'

    def set_publication_ids(self, n):
        self.num = n
        self.id = 'PGP' + str(n).zfill(6)

    def is_published(self):
        return self.PMID != None

    @property
    def is_preprint(self):
        return 'bioRxiv' in self.journal or 'medRxiv' in self.journal

    @property
    def pub_year(self):
        return self.date_publication.strftime('%Y')

    @property
    def scores_count(self):
        return self.publication_score.all().count()

    @property
    def scores_evaluated(self):
        # Using 'all()' and filter afterward uses less SQL queries than a direct distinct()
        score_ids_set = set()
        for performance in self.publication_performance.all():
            score_ids_set.add(performance.score.id)
        return len(list(score_ids_set))

    @property
    def associated_pgs_ids(self):
        # Using 'all' and filter afterward uses less SQL queries than a direct distinct()
        score_ids_set = set()
        for score in self.publication_score.all():
            score_ids_set.add(score.id)
        return list(score_ids_set)

    def parse_EuropePMC(self, doi=None, PMID=None):
        '''Function to get the citation information from the EuropePMC API'''
        import requests

        payload = {'format': 'json'}
        if doi != None:
            payload['query'] = 'doi:' + doi
        elif type(PMID) == int:
            payload['query'] = ['ext_id:' + str(PMID)]
        else:
            print('Please retry with a valid doi or PMID')

        if 'query' in payload:
            r = requests.get('https://www.ebi.ac.uk/europepmc/webservices/rest/search', params=payload)
            r = r.json()
            r = r['resultList']['result'][0]

            self.doi = r['doi']
            self.firstauthor = r['authorString'].split(',')[0]
            self.authors = r['authorString']
            self.title = r['title']
            self.date_publication = r['firstPublicationDate']

            if r['pubType'] == 'preprint':
                self.journal=r['bookOrReportDetails']['publisher']
            else:
                self.journal=r['journalTitle']
                if 'pmid' in r:
                    self.PMID=r['pmid']


class Cohort(models.Model):
    """Class to describe cohorts used in samples"""
    name_short = models.CharField('Cohort Short Name', max_length=100, db_index=True)
    name_full = models.CharField('Cohort Full Name', max_length=1000)

    def __str__(self):
        return self.name_short

    @property
    def associated_pgs_ids(self):

        list_dev_associated_pgs_ids  = set()
        list_eval_associated_pgs_ids = set()
        sample_ids_list = set()
        pss_ids_list = set()

        for sample in self.sample_set.all():
            if sample.id in sample_ids_list:
                continue
            list_pgs_ids = sample.associated_PGS()
            for pgs_id in list_pgs_ids:
                if pgs_id != '':
                    list_dev_associated_pgs_ids.add(pgs_id)

            pss_ids = sample.associated_PSS()
            for pss_id in pss_ids:
                pss_ids_list.add(pss_id)

            sample_ids_list.add(sample.id)

        list_dev_associated_pgs_ids = list(list_dev_associated_pgs_ids)
        list_dev_associated_pgs_ids.sort()

        sample_sets = SampleSet.objects.filter(id__in=list(pss_ids_list)).distinct()
        perfs = Performance.objects.select_related('score').values('score__id').filter(sampleset__in=sample_sets).distinct()

        for perf in perfs:
            list_eval_associated_pgs_ids.add(perf['score__id'])

        list_eval_associated_pgs_ids = list(list_eval_associated_pgs_ids)
        list_eval_associated_pgs_ids.sort()

        return { 'development': list_dev_associated_pgs_ids, 'evaluation': list_eval_associated_pgs_ids}


class EFOTrait(models.Model):
    '''Class to hold information related to controlled trait vocabulary
    (mainly to link multiple EFO to a single score)'''
    id = models.CharField('Ontology Trait ID', max_length=30, primary_key=True)
    label = models.CharField('Ontology Trait Label', max_length=500, db_index=True)
    description = models.TextField('Ontology Trait Description', null=True)
    url = models.CharField('Ontology URL', max_length=500)
    synonyms = models.TextField('Synonyms', null=True)
    mapped_terms = models.TextField('Mapped terms', null=True)


    def parse_api(self):
        import requests
        response = requests.get('https://www.ebi.ac.uk/ols/api/ontologies/efo/terms?obo_id=%s'%self.id.replace('_', ':'))
        response = response.json()['_embedded']['terms']
        if len(response) == 1:
            response = response[0]
            self.label = response['label']
            self.url = response['iri']

            # Make description
            try:
                desc = response['obo_definition_citation'][0]
                str_desc = desc['definition']
                for x in desc['oboXrefs']:
                    if x['database'] != None:
                        if x['id'] != None:
                            str_desc += ' [{}: {}]'.format(x['database'], x['id'])
                        else:
                            str_desc += ' [{}]'.format(x['database'])
                self.description = str_desc
            except:
                self.description = response['description']


    def __str__(self):
        return '%s | %s '%(self.id, self.label)

    @property
    def display_label(self):
        return '<a href="../../trait/%s">%s</a>'%(self.id, self.label)

    def display_id_url(self):
        return '<a href="%s">%s</a><span class="only_export">: %s</span>'%(self.url, self.id, self.url)

    @property
    def synonyms_list(self):
        if self.synonyms:
            return self.synonyms.split(' | ')
        else:
            return []

    @property
    def mapped_terms_list(self):
        if self.mapped_terms:
            return self.mapped_terms.split(' | ')
        else:
            return []

    @property
    def associated_pgs_ids(self):
        # Using 'all' and filter afterward uses less SQL queries than a direct distinct()
        score_ids_set = set()
        for score in self.score_set.all():
            score_ids_set.add(score.id)
        return list(score_ids_set)

    @property
    def scores_count(self):
        return self.score_set.count()

    @property
    def category_labels(self):
        categories = self.traitcategory_set.all()
        categories_data = ''
        if len(categories) > 0:
            category_labels = [x.label for x in categories]
            categories_data = ', '.join(category_labels)

        return categories_data

    @property
    def category_list(self):
        return self.traitcategory_set.all()


class TraitCategory(models.Model):
    # Stable identifiers for declaring a set of traits
    label = models.CharField('Trait category', max_length=50, db_index=True)
    colour = models.CharField('Trait category colour', max_length=30)
    parent = models.CharField('Trait category (parent term)', max_length=50)

    # Link to the description of the sample(s) in the other table
    efotraits = models.ManyToManyField(EFOTrait, verbose_name='Traits')

    class Meta:
        verbose_name_plural = "Trait categories"

    def __str__(self):
        return self.label

    @property
    def count_scores(self):
        scores_count = 0
        for trait in self.efotraits.all():
            scores_count += trait.scores_count

        return scores_count


class Demographic(models.Model):
    """Class to describe Sample fields (sample_age, followup_time) that can be point estimates or distributions"""
    estimate = models.FloatField(verbose_name='Estimate (value)', null=True)
    estimate_type = models.CharField(verbose_name='Estimate (type)', max_length=100, null=True, default='mean') #e.g. [mean, median]
    unit = models.TextField(verbose_name='Unit', max_length=100, null=False, default='years') # e.g. [years, months, days]

    range = DecimalRangeField(verbose_name='Range (values)', null=True)
    range_type = models.CharField(verbose_name='Range (type)', max_length=100, default='range') # e.g. Confidence interval (ci), range, interquartile range (iqr), open range

    variability = models.FloatField(verbose_name='Variability (value)', null=True)
    variability_type = models.CharField(verbose_name='Range (type)', max_length=100, default='se') # e.g. standard deviation (sd), standard error (se)

    def format_estimate(self):
        if self.estimate != None:
            return '{}:{}'.format(self.estimate_type, self.estimate)
        return None

    def format_range(self):
        if self.estimate == None and self.range != None:
            return '{}:{}'.format(self.range_type, str(self.range))
        return None

    def format_variability(self):
        if self.variability != None:
            return '{}:{}'.format(self.variability_type, self.variability)
        return None

    def format_unit(self):
        if self.unit != None:
            return '{}:{}'.format('unit', self.unit)
        return None


    def display_value(self):
        l = []
        helptip    = '<span title="{}" class="pgs_helptip">{}</span> : {} {}'
        no_helptip = '{} : {} {}'

        # Estimate
        e = ''
        if self.estimate != None:
            e += '{} : {}'.format(self.estimate_type.title(), self.estimate)
            if self.range != None and self.range_type.lower() == 'ci':
                e += ' {}'.format(str(self.range))
            e += ' {}'.format(self.unit)
        if len(e) > 0:
            l.append(e)

        # Variability
        v = None
        if self.variability != None:
            type_desc = self.variability_type_desc()
            if (type_desc):
                v = helptip.format(type_desc, self.variability_type.title(), self.variability, self.unit)
            else:
                v = no_helptip.format(self.variability_type.title(), self.variability, self.unit)
        if v != None:
            l.append(v)

        # Range
        r = None
        if '[' not in e:
            if self.range != None:
                type_desc = self.range_type_desc()
                if (type_desc):
                    r = helptip.format(type_desc, self.range_type.title(), str(self.range), self.unit)
                else:
                    r = no_helptip.format(self.range_type.title(), str(self.range), self.unit)
        if r != None:
            l.append(r)

        if (len(l) == 1):
            return l[0]
        elif (len(l) > 1):
            return '<ul><li>'+'</li><li>'.join(l)+'</li></ul>'
        else:
            return ''

    def display_values_dict(self):
        l = {}

        # Estimate
        estimate = ''
        if self.estimate != None:
            estimate = str(self.estimate)
            if self.range != None and self.range_type.lower() == 'ci':
                estimate += str(self.range)
            if estimate:
                l[self.estimate_type] = estimate

        # Range
        if self.range != None and '[' not in estimate:
            l[self.range_type] = str(self.range)

        # Variability
        if self.variability != None:
            l[self.variability_type] = self.variability

        # Unit
        if self.unit != None:
            l['unit'] = self.unit

        return l


    def range_type_desc(self):
        desc_list = {
            'ci': 'Confidence interval',
            'iqr': 'Interquartile range'
        }
        if self.range_type.lower() in desc_list:
            return desc_list[self.range_type.lower()]

    def variability_type_desc(self):
        desc_list = {
            'sd': 'Standard Deviation',
            'sd (cases)': 'Standard Deviation',
            'se': 'Standard Error',
        }
        if self.variability_type.lower() in desc_list:
            return desc_list[self.variability_type.lower()]


class Sample(models.Model):
    """Class to describe samples used in variant associations and PGS training/testing"""

    # Sample Information
    ## Numbers
    sample_number = models.IntegerField('Number of Individuals', validators=[MinValueValidator(1)])
    sample_cases = models.IntegerField('Number of Cases', null=True)
    sample_controls = models.IntegerField('Number of Controls', null=True)
    sample_percent_male = models.FloatField('Percent of Participants Who are Male', validators=[MinValueValidator(0), MaxValueValidator(100)], null=True)
    sample_age = models.OneToOneField(Demographic, on_delete=models.CASCADE,related_name='ages_of', null=True)

    ## Description
    phenotyping_free = models.TextField('Detailed Phenotype Description', null=True)
    followup_time = models.OneToOneField(Demographic, on_delete=models.CASCADE,related_name='followuptime_of', null=True)

    ## Ancestry
    ancestry_broad = models.CharField('Broad Ancestry Category', max_length=100)
    ancestry_free = models.TextField('Ancestry (e.g. French, Chinese)', null=True)
    ancestry_country = models.TextField('Country of Recruitment', null=True)
    ancestry_additional = models.TextField('Additional Ancestry Description', null=True)

    ## Cohorts/Sources
    source_GWAS_catalog = models.CharField('GWAS Catalog Study ID (GCST...)', max_length=20, null=True)
    source_PMID = models.CharField('Source PubMed ID (PMID) or doi', max_length=100, null=True)
    cohorts = models.ManyToManyField(Cohort, verbose_name='Cohort(s)')
    cohorts_additional = models.TextField('Additional Sample/Cohort Information', null=True)

    def __str__(self):
        s = 'Sample: {}'.format(str(self.pk))

        #Check if any PGS
        ids = self.associated_PGS()
        if len(ids) > 0:
            s += ' | {}'.format(' '.join(ids))
        # Check if any PSS
        ids = self.associated_PSS()
        if len(ids) > 0:
            s += ' | {}'.format(' '.join(ids))
        return s

    def associated_PGS(self):
        ids = set()
        for x in self.score_variants.all():
            ids.add(x.id)
        for x in self.score_training.all():
            ids.add(x.id)
        ids = list(ids)
        ids.sort()
        return ids

    def associated_PSS(self):
        ids = set()
        for x in self.sampleset.all():
            ids.add(x.id)
        ids = list(ids)
        ids.sort()
        return ids

    def list_cohortids(self):
        return [x.name_short for x in self.cohorts.all()]

    @property
    def display_sampleset(self):
        return self.sampleset.all()[0]

    @property
    def display_samples(self):
        sinfo = ['{:,} individuals'.format(self.sample_number)]
        if self.sample_cases != None:
            sstring = '[ {:,} cases'.format(self.sample_cases)
            if self.sample_controls != None:
                sstring += ', {:,} controls ]'.format(self.sample_controls)
            else:
                sstring += ' ]'
            sinfo.append(sstring)
        if self.sample_percent_male != None:
            sinfo.append('%s %% Male samples'%str(round(self.sample_percent_male,2)))
        return sinfo

    @property
    def display_samples_for_table(self):
        div_id = "sample_"+str(self.pk)
        sstring = ''
        if self.sample_cases != None:
            sstring += '<div><a class="toggle_table_btn pgs_helptip" id="'+div_id+'" title="Click to show/hide the details">{:,} individuals <i class="fa fa-plus-circle"></i></a></div>'.format(self.sample_number)
            sstring += '<div class="toggle_list" id="list_'+div_id+'">'
            sstring += '<span class="only_export">[</span>'
            sstring += '<ul>\n<li>{:,} cases</li>\n'.format(self.sample_cases)
            if self.sample_controls != None:
                sstring += '<li><span class="only_export">, </span>'
                sstring += '{:,} controls</li>'.format(self.sample_controls)
            sstring += '</ul>'
            sstring += '<span class="only_export">]</span>'
            sstring += '</div>'
        else:
            sstring += '{:,} individuals'.format(self.sample_number)
        if self.sample_percent_male != None:
            sstring += '<span class="only_export">, </span>'
            sstring += '<div class="mt-2 smaller-90">%s %% Male samples</div>'%str(round(self.sample_percent_male,2))
        return sstring

    @property
    def display_sample_number_total(self):
        ssinfo = '{:,} individuals'.format(self.sample_number)
        return ssinfo

    @property
    def display_sample_number_detail(self):
        sinfo = []
        if self.sample_cases != None:
            sinfo.append('{:,} cases'.format(self.sample_cases))
            if self.sample_controls != None:
                sinfo.append('{:,} controls'.format(self.sample_controls))
        if self.sample_percent_male != None:
            sinfo.append('%s %% Male samples'%str(round(self.sample_percent_male,2)))
        return sinfo

    @property
    def display_sample_category_number(self):
        categories = []
        numbers = []
        if self.sample_cases != None:
            #sinfo['Cases'] = self.sample_cases
            categories.append("Cases")
            numbers.append(self.sample_cases)
            if self.sample_controls != None:
                #sinfo['Controls'] = self.sample_controls
                categories.append('Controls')
                numbers.append(self.sample_controls)
        return [categories,numbers]

    @property
    def display_sample_gender_percentage(self):
        categories = []
        numbers = []
        if self.sample_percent_male != None:
            percent_male = round(self.sample_percent_male,2)
            categories = ["% Male", "% Female"]
            numbers    = [percent_male, round(100-percent_male,2)]
        return [categories,numbers]


    @property
    def display_sources(self):
        d = {}
        if self.source_GWAS_catalog:
            d['GCST'] = self.source_GWAS_catalog
        if self.source_PMID:
            d['PMID'] = self.source_PMID
        return d

    @property
    def display_ancestry(self):
        if self.ancestry_free in ['NR', '', None]:
            return self.ancestry_broad
        else:
            return '{}<br/>({})'.format(self.ancestry_broad, self.ancestry_free)

    @property
    def display_ancestry_inline(self):
        if self.ancestry_free in ['NR', '', None]:
            return self.ancestry_broad
        else:
            return '{} ({})'.format(self.ancestry_broad, self.ancestry_free)


class Score(models.Model):
    """Class for individual Polygenic Score (PGS)"""

    # Stable identifiers
    num = models.IntegerField('Polygenic Score (PGS) Number', primary_key=True)
    id = models.CharField('Polygenic Score (PGS) ID', max_length=30, db_index=True)

    name = models.CharField('PGS Name', max_length=100)

    # Curation/release information
    date_released = models.DateField('PGS Catalog Release Date', null=True, db_index=True)
    curation_notes = models.TextField('Curation Notes', default='')

    # Links to related models
    publication = models.ForeignKey(Publication, on_delete=models.PROTECT, related_name='publication_score', verbose_name='PGS Publication (PGP) ID')
    ## Contributing Samples
    samples_variants = models.ManyToManyField(Sample, verbose_name='Source of Variant Associations (GWAS)', related_name='score_variants')
    samples_training = models.ManyToManyField(Sample, verbose_name='Score Development/Training', related_name='score_training')

    # Trait information
    trait_reported = models.TextField('Reported Trait')
    trait_additional = models.TextField('Additional Trait Information', null=True)
    trait_efo = models.ManyToManyField(EFOTrait, verbose_name='Mapped Trait(s) (EFO terms)')

    # PGS Development/method details
    method_name = models.TextField('PGS Development Method')
    method_params = models.TextField('PGS Development Details/Relevant Parameters', default='NR')

    variants_number = models.IntegerField('Number of Variants', validators=[MinValueValidator(1)])
    variants_interactions = models.IntegerField('Number of Interaction Terms', default=0)
    variants_genomebuild = models.CharField('Original Genome Build', max_length=10, default='NR')

    # Methods
    def __str__(self):
        return ' | '.join([self.id, self.name, '(%s)' % self.publication.__str__()])

    def set_score_ids(self, n):
        self.num = n
        self.id = 'PGS' + str(n).zfill(6)


    class Meta:
        get_latest_by = 'num'

    # Score file FTP addresses
    @property
    def link_filename(self):
        filename = self.id + '.txt.gz'
        return filename

    @property
    def ftp_scoring_file(self):
        ftp_url = '{}/scores/{}/ScoringFiles/{}'.format(settings.USEFUL_URLS['PGS_FTP_HTTP_ROOT'], self.id, self.link_filename)
        return ftp_url

    @property
    def list_traits(self):
        l = [] # tuples (id, label)
        for t in self.trait_efo.all():
            l.append((t.id, t.label))
        return(l)


class SampleSet(models.Model):
    # Stable identifiers for declaring a set of related samples
    num = models.IntegerField('PGS Sample Set (PSS) Number', primary_key=True)
    id = models.CharField('PGS Sample Set (PSS) ID', max_length=30, db_index=True)

    # Link to the description of the sample(s) in the other table
    samples = models.ManyToManyField(Sample, verbose_name='Sample Set Descriptions', related_name='sampleset')

    def __str__(self):
        return self.id

    def set_ids(self, n):
        self.num = n
        self.id = 'PSS' + str(n).zfill(6)

    @property
    def samples_ancestry(self):
        ancestry_list = []
        for sample in self.samples.all():
            ancestry = sample.display_ancestry_inline
            if ancestry and ancestry not in ancestry_list:
                ancestry_list.append(ancestry)
        if len(ancestry_list) > 0:
            return ', '.join(ancestry_list)
        else:
            return '-'

    @property
    def count_samples(self):
        return len(self.samples.all())

    @property
    def count_performances(self):
        return len(Performance.objects.values('id').filter(sampleset_id=self.num))


class Performance(models.Model):
    """Class to hold performance/accuracy metrics for a PGS and a set of samples"""
    # Key identifiers
    num = models.IntegerField('PGS Performance Metric (PPM) Number', primary_key=True)
    id = models.CharField('PGS Performance Metric (PPM) ID', max_length=30, db_index=True)

    # Curation information
    date_released = models.DateField('PGS Catalog Release Date', null=True, db_index=True)
    curation_notes = models.TextField('Curation Notes', default='')

    # Links to related objects
    score = models.ForeignKey(Score, on_delete=models.CASCADE,
                              verbose_name='Evaluated Score') # PGS that the metrics are associated with
    phenotyping_efo = models.ManyToManyField(EFOTrait, verbose_name='Mapped Trait(s) (EFO)')
    sampleset = models.ForeignKey(SampleSet, on_delete=models.PROTECT, verbose_name='PGS Sample Set (PSS)',
                                    related_name='sampleset_performance') # Samples used for evaluation
    publication = models.ForeignKey(Publication, on_delete=models.PROTECT, verbose_name='Peformance Source',
                                    related_name='publication_performance') # Study that reported performance metrics

    # [Links to Performance metrics are made by ForeignKey in Metrics table, previously they were parameterized here]
    phenotyping_reported = models.CharField('Reported Trait', max_length=200)
    covariates = models.TextField('Covariates Included in the Model', null=True)
    performance_comments = models.TextField('PGS Performance: Other Relevant Information', null=True)

    def __str__(self):
        return '%s | %s -> %s'%(self.id, self.score.id, self.sampleset.id)

    class Meta:
        get_latest_by = 'num'

    def set_performance_id(self, n):
        self.num = n
        self.id = 'PPM' + str(n).zfill(6)\

    def samples(self):
        """ Method working as a shortcut to fetch all the samples related to the sampleset  """
        return list(self.sampleset.samples.all())

    @property
    def associated_pgs_id(self):
        return self.score.id

    @property
    def display_trait(self):
        d = {}
        if self.phenotyping_reported != '':
            d['reported'] = self.phenotyping_reported
        # Using all and filter afterward uses less SQL queries than a direct distinct()
        efo_traits = self.phenotyping_efo.all()
        if efo_traits:
            traits_set = set()
            for trait in efo_traits:
                traits_set.add(trait)
            d['efo'] = list(traits_set)
        return d

    @property
    def effect_sizes_list(self):
        return self.get_metric_data('Effect Size')

    @property
    def class_acc_list(self):
        return self.get_metric_data('Classification Metric')

    @property
    def othermetrics_list(self):
        return self.get_metric_data('Other Metric')


    @property
    def performance_metrics(self):
        perf_metrics = {}

        effect_sizes_list = self.effect_sizes_list
        effect_sizes_data = []
        if effect_sizes_list:
            for effect_size in self.effect_sizes_list:
                effect_sizes_data.append({'labels': effect_size[0], 'value': effect_size[1]})
        perf_metrics['effect_sizes'] = effect_sizes_data

        class_acc_list = self.class_acc_list
        class_acc_data = []
        if class_acc_list:
            for class_acc in self.class_acc_list:
                class_acc_data.append({'labels': class_acc[0], 'value': class_acc[1]})
        perf_metrics['class_acc'] = class_acc_data

        othermetrics_list = self.othermetrics_list
        othermetrics_data = []
        if othermetrics_list:
            for othermetrics in othermetrics_list:
                othermetrics_data.append({'labels': othermetrics[0], 'value': othermetrics[1]})
        perf_metrics['othermetrics'] = othermetrics_data

        return perf_metrics


    @property
    def publication_withexternality(self):
        '''This function checks whether the evaluation is internal or external to the score development paper'''
        p = self.publication
        info = [' '.join([p.id, '<br/><small><i class="fa fa-angle-double-right"></i> ',p.firstauthor, '<i>et al.</i>', '(%s)' % p.date_publication.strftime('%Y'), '</small>']), self.publication.id]

        if self.publication == self.score.publication:
            info.append('D')
        else:
            info.append('E')

        if self.publication.is_preprint:
            info.append('<span class="badge badge-pgs-small-2 ml-1" data-toggle="tooltip" title="Preprint (manuscript has not undergone peer review)">Pre</span>')
        else:
            info.append('')

        return '|'.join(info)


    def get_metric_data(self, metric_type):
        """ Generic method to extract and format the diverse metric data"""
        # Using all and filter afterward uses less SQL queries than filtering directly on the queryset
        metrics = self.performance_metric.all()
        if metrics:
            l = []
            for m in metrics:
                if (m.type == metric_type):
                    l.append((m.name_tuple(), m.display_value()))
            if len(l) != 0:
                return l
        return None


class Metric(models.Model):
    """Class to hold metric type, name, value and confidence intervals of a performance metric"""
    performance = models.ForeignKey(Performance, on_delete=models.CASCADE, verbose_name='PGS Performance Metric (PPM)', related_name="performance_metric")

    TYPE_CHOICES = [
        ('ES', 'Effect Size'),
        ('CM', 'Classification Metric'),
        ('OM', 'Other Metric')
    ]
    type = models.CharField(max_length=40,
        choices=TYPE_CHOICES,
        default='Other Metric',
        db_index=True
    )

    name = models.CharField(verbose_name='Performance Metric Name', max_length=100, null=False) # ex: "Odds Ratio"
    name_short = models.CharField(verbose_name='Performance Metric Name (Short)', max_length=10, null=True) # ex: "OR"

    estimate = models.FloatField(verbose_name='Estimate', null=False)
    unit = models.TextField(verbose_name='Units of the effect size', max_length=100, blank = False)
    ci = DecimalRangeField(verbose_name='95% Confidence Interval', null=True)
    se = models.FloatField(verbose_name='Standard error of the effect', null=True)

    def __str__(self):
        if self.ci != None:
            s = '{} {}'.format(self.estimate, self.ci)
        else:
            s = '{}'.format(self.estimate)

        if (self.name_short):
            return '%s (%s): %s'%(self.name, self.name_short, s)
        else:
            return '%s: %s'%(self.name, s)

    def display_value(self):
        if self.ci != None:
            s = '{} {}'.format(self.estimate, self.ci)
        else:
            s = '{}'.format(self.estimate)
        return s

    def name_tuple(self):
        if self.name_short is None:
            return (self.name, self.name)
        else:
            return (self.name, self.name_short)


class Release(models.Model):
    """Class to store and manipulate the releases information"""
    date = models.DateField("Release date", null=False, db_index=True)
    score_count = models.IntegerField('Number of new PGS scores released', default=0)
    performance_count = models.IntegerField('Number of new PGS Performance metrics released', default=0)
    publication_count = models.IntegerField('Number of new PGS Publication released', default=0)
    notes = models.TextField(verbose_name='Release notes', max_length=600, blank=True)
    updated_score_count = models.IntegerField('Number of PGS scores updated', default=0)
    updated_performance_count = models.IntegerField('Number of PGS Performance metrics updated', default=0)
    updated_publication_count = models.IntegerField('Number of PGS Publication updated', default=0)

    def __str__(self):
        return str(self.date)

    @property
    def released_score_ids(self):
        scores = Score.objects.values('id').filter(date_released__exact=self.date).order_by('id')
        return [x['id'] for x in scores]

    @property
    def released_publication_ids(self):
        publications = Publication.objects.values('id').filter(date_released__exact=self.date).order_by('id')
        return [x['id'] for x in publications]

    @property
    def released_performance_ids(self):
        performances = Performance.objects.values('id').filter(date_released__exact=self.date).order_by('id')
        return [x['id'] for x in performances]
