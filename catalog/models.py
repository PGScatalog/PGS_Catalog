import datetime
from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.postgres.fields import DecimalRangeField
from pgs_web import constants
from catalog import common


class Publication(models.Model):
    """Class for publications with PGS"""
    # Stable identifiers
    num = models.IntegerField('PGS Publication/Study Number (PGP)', primary_key=True)
    id = models.CharField('PGS Publication/Study ID (PGP)', max_length=30, db_index=True)

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
        ('AW', 'Awaiting Curation'),
        ('E',  'Embargoed')
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
        # Dependant on the context, sometimes the date_publication is returned as a string
        pub_date = self.date_publication
        if type(pub_date) == str:
            pub_date = datetime.datetime.strptime(pub_date, '%Y-%m-%d')
        return pub_date.strftime('%Y')

    @property
    def scores_count(self):
        return self.publication_score.count()

    @property
    def scores_evaluated_count(self):
        # Different from scores_evaluated as it is faster this way with several calls
        score_ids_set = set(performance.score.id for performance in self.publication_performance.all())
        return len(score_ids_set)

    @property
    def scores_evaluated(self):
        # Shortcut by using EvaluatedScore
        score_ids_list = self.publication_evaluatedscore.values_list('scores_evaluated__id', flat=True).all().order_by('scores_evaluated__id')
        return score_ids_list

    @property
    def scores_developed(self):
        score_ids_list = self.publication_score.values_list('id', flat=True).all().distinct().order_by('id')
        return score_ids_list

    @property
    def associated_pgs_ids(self):
        return { 'development': self.scores_developed, 'evaluation': self.scores_evaluated }

    def parse_EuropePMC(self, doi=None, PMID=None):
        """Function to get the citation information from the EuropePMC API"""
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
    name_others = models.TextField('Previous/other/additional names (e.g. sub-cohorts)', null=True)

    # Used to identify cohorts with associated released scores
    released = models.BooleanField('Associated with released Score(s)', default=False)

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
            for pgs_id in sample.associated_PGS():
                if pgs_id == '':
                    continue
                list_dev_associated_pgs_ids.add(pgs_id)

            for pss_id in sample.associated_PSS():
                pss_ids_list.add(pss_id)

            sample_ids_list.add(sample.id)

        # Development association
        list_dev_associated_pgs_ids = sorted(list_dev_associated_pgs_ids)

        # Evaluation association
        list_eval_associated_pgs_ids = Performance.objects.select_related('score').values_list('score__id', flat=True).filter(sampleset__id__in=list(pss_ids_list)).distinct().order_by('score__id')

        return { 'development': list_dev_associated_pgs_ids, 'evaluation': list(list_eval_associated_pgs_ids)}


class EFOTrait_Base(models.Model):
    """Abstract class to hold information related to controlled trait vocabulary
    (mainly to link multiple EFO to a single score)"""
    id = models.CharField('Ontology Trait ID', max_length=30, primary_key=True)
    label = models.CharField('Ontology Trait Label', max_length=500, db_index=True)
    description = models.TextField('Ontology Trait Description', null=True)
    url = models.CharField('Ontology URL', max_length=500)
    synonyms = models.TextField('Synonyms', null=True)
    mapped_terms = models.TextField('Mapped terms', null=True)

    class Meta:
        abstract = True

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
    def id_colon(self):
        return self.id.replace('_',':')

    @property
    def display_label(self):
        return '<a href="/trait/%s">%s</a>'%(self.id, self.label)

    @property
    def display_ext_url(self):
        if not self.id.startswith('EFO'):
            url = 'https://www.ebi.ac.uk/ols/ontologies/efo/terms?iri='+self.url
        else:
            url = self.url
        return '<a href="%s">%s</a>'%(url, self.id)

    @property
    def description_list(self):
        if self.description:
            return self.description.split(' | ')
        else:
            return []

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
    def category_list(self):
        return sorted(self.traitcategory.all(), key=lambda y: y.label)

    @property
    def category_labels_list(self):
        categories = self.category_list
        if len(categories) > 0:
            return [x.label for x in categories]
        else:
            return []

    @property
    def category_labels(self):
        category_labels = self.category_labels_list
        categories_data = ''
        if len(category_labels) > 0:
            categories_data = ', '.join(category_labels)

        return categories_data

    @property
    def display_category_labels(self):
        categories = self.category_list
        categories_data = ''
        if len(categories) > 0:
            category_labels = []
            for category in categories:
                v_spacing = ' class="mt-1"' if len(category_labels) > 0 else ''
                category_labels.append('<div{}><span class="trait_colour" style="background-color:{}"></span>{}</div>'.format(v_spacing,category.colour,category.label))
            categories_data = ''.join(category_labels)

        return categories_data


class EFOTrait(EFOTrait_Base):
    """Implementation of the abstract class 'EFOTrait_Base' to hold information related to controlled trait vocabulary
    (mainly to link multiple EFO to a single score)"""

    @property
    def associated_pgs_ids(self):
        # Using 'all' and filter afterward uses less SQL queries than a direct distinct()
        score_ids_set = set(score.id for score in self.associated_scores.all())
        return sorted(score_ids_set)

    @property
    def scores_count(self):
        return self.associated_scores.count()


class Demographic(models.Model):
    """Class to describe Sample fields (sample_age, followup_time) that can be point estimates or distributions"""
    estimate = models.FloatField(verbose_name='Estimate (value)', null=True)
    estimate_type = models.CharField(verbose_name='Estimate (type)', max_length=100, null=True, default='mean') #e.g. [mean, median]
    unit = models.TextField(verbose_name='Unit', max_length=100, null=False, default='years') # e.g. [years, months, days]

    range = DecimalRangeField(verbose_name='Range (values)', null=True)
    range_type = models.CharField(verbose_name='Range (type)', max_length=100, default='range') # e.g. Confidence interval (ci), range, interquartile range (iqr), open range

    variability = models.FloatField(verbose_name='Variability (value)', null=True)
    variability_type = models.CharField(verbose_name='Variablility (type)', max_length=100, default='se') # e.g. standard deviation (sd), standard error (se)

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
        return '{}:{}'.format('unit', self.unit)


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
            estimate = self.estimate
            if self.range != None and self.range_type.lower() == 'ci':
                estimate = f'{estimate} {self.range}'
            if estimate:
                l['estimate_type'] = self.estimate_type.lower()
                l['estimate'] = estimate

        # Range
        if self.range != None and '[' not in str(estimate):
            l['interval'] = {
                'type': self.range_type.lower(),
                'lower': float(self.range.lower),
                'upper': float(self.range.upper)
            }
        # Variability
        if self.variability != None:
            l['variability_type'] = self.variability_type.lower()
            l['variability'] = self.variability

        # Unit
        if self.unit != None:
            l['unit'] = self.unit.lower()

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
    sample_number = models.IntegerField('Number of Individuals', null=True)
    sample_cases = models.IntegerField('Number of Cases', null=True)
    sample_controls = models.IntegerField('Number of Controls', null=True)
    sample_percent_male = models.FloatField('Percent of Participants Who are Male', validators=[MinValueValidator(0), MaxValueValidator(100)], null=True)
    sample_age = models.OneToOneField(Demographic, on_delete=models.CASCADE,related_name='ages_of', null=True)

    ## Description
    phenotyping_free = models.TextField('Phenotype Definitions and Methods', null=True)
    followup_time = models.OneToOneField(Demographic, on_delete=models.CASCADE,related_name='followuptime_of', null=True)

    ## Ancestry
    ancestry_broad = models.CharField('Broad Ancestry Category', max_length=250)
    ancestry_free = models.TextField('Ancestry (e.g. French, Chinese)', null=True)
    ancestry_country = models.TextField('Country of Recruitment', null=True)
    ancestry_additional = models.TextField('Additional Ancestry Description', null=True)

    ## Cohorts/Sources
    source_GWAS_catalog = models.CharField('GWAS Catalog Study ID (GCST...)', max_length=20, null=True)
    source_PMID = models.IntegerField('Source PubMed ID (PMID)', null=True)
    source_DOI = models.CharField('Source DOI', max_length=100, null=True)
    cohorts = models.ManyToManyField(Cohort, verbose_name='Cohort(s)')
    cohorts_additional = models.TextField('Additional Sample/Cohort Information', null=True)

    def __str__(self):
        s = 'Sample {}'.format(str(self.pk))
        if self.ancestry_broad:
            s += ' - {}'.format(self.ancestry_broad)
        s += ' '+self.display_sample_number_total
        return s

    def associated_PGS(self):
        ids = set()
        for x in self.score_variants.all():
            ids.add(x.id)
        for x in self.score_training.all():
            ids.add(x.id)
        ids = sorted(ids)
        return ids

    def associated_PSS(self):
        ids = set()
        for x in self.sampleset.all():
            ids.add(x.id)
        ids = sorted(ids)
        return ids

    def list_cohortids(self):
        return [x.name_short for x in self.cohorts.all()]

    @property
    def sample_cases_percent(self):
        if self.sample_cases != None:
            percent = (self.sample_cases / self.sample_number) * 100
            return round(percent,2)
        else:
            return None

    @property
    def display_sampleset(self):
        samplesets = self.sampleset.all()
        if samplesets:
            return samplesets[0]
        else:
            return None

    @property
    def display_samples(self):
        sinfo = [common.individuals_format(self.sample_number)]
        if self.sample_cases != None:
            sstring = '[ {:,} cases'.format(self.sample_cases)
            if self.sample_controls != None:
                sstring += ', {:,} controls'.format(self.sample_controls)
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
            sstring += '<div><a class="toggle_table_btn pgs_btn_plus pgs_helptip" id="{}" title="Click to show/hide the details">{}</a></div>'.format(div_id,common.individuals_format(self.sample_number))
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
            sstring += self.display_sample_number_total
        if self.sample_percent_male != None:
            sstring += '<span class="only_export">, </span>'
            sstring += '<div class="mt-2 smaller-90">%s %% Male samples</div>'%str(round(self.sample_percent_male,2))
        return sstring

    @property
    def display_sample_number_total(self):
        ssinfo = 'NR'
        if self.sample_number != None:
            ssinfo = common.individuals_format(self.sample_number)
        return ssinfo

    @property
    def display_sample_number_detail(self):
        sinfo = []
        if self.sample_cases != None:
            sinfo.append('<div class="sample_cases">{:,} cases ({}%)</div>'.format(self.sample_cases, self.sample_cases_percent))
            if self.sample_controls != None:
                sinfo.append('<div class="sample_controls">{:,} controls</div>'.format(self.sample_controls))
        if self.sample_percent_male != None:
            sinfo.append('<div class="sample_male">%s%% Male samples</div>'%str(round(self.sample_percent_male,2)))
        return sinfo

    @property
    def display_sample_category_number(self):
        data = []
        if self.sample_cases != None:
            data.append({'name': 'Cases', 'value': self.sample_cases})
            if self.sample_controls != None:
                data.append({'name': 'Controls', 'value': self.sample_controls})
        return data

    @property
    def display_sample_gender_percentage(self):
        data = []
        if self.sample_percent_male != None:
            percent_male = round(self.sample_percent_male,2)
            data = [
                { 'name': '% Male', 'value': percent_male },
                { 'name': '% Female', 'value': round(100-percent_male,2) }
            ]
        return data


    @property
    def display_sources(self):
        d = {}
        if self.source_GWAS_catalog:
            d['GCST'] = self.source_GWAS_catalog
        if self.source_PMID:
            d['PMID'] = self.source_PMID
        if self.source_DOI:
            d['DOI'] = self.source_DOI
        return d

    @property
    def display_ancestry(self):
        if self.ancestry_free in ['NR', '', None]:
            return self.ancestry_broad
        else:
            return '{}<br/><small>({})</small>'.format(self.ancestry_broad, self.ancestry_free)

    @property
    def display_ancestry_inline(self):
        if self.ancestry_free in ['NR', '', None]:
            return self.ancestry_broad
        else:
            return '{} <small>({})</small>'.format(self.ancestry_broad, self.ancestry_free)


class Score(models.Model):
    """Class for individual Polygenic Score (PGS)"""

    # Stable identifiers
    num = models.IntegerField('Polygenic Score (PGS) Number', primary_key=True)
    id = models.CharField('Polygenic Score (PGS) ID', max_length=30, db_index=True)

    name = models.CharField('PGS Name', max_length=100)

    # Curation/release information
    date_released = models.DateField('PGS Catalog Release Date', null=True, db_index=True)
    curation_notes = models.TextField('Curation Notes', default='')

    # Used to identify scores that don't match the original publication
    flag_asis = models.BooleanField('Score and results match the original publication', default=True)

    # Links to related models
    publication = models.ForeignKey(Publication, on_delete=models.PROTECT, related_name='publication_score', verbose_name='PGS Publication ID (PGP)')
    ## Contributing Samples
    samples_variants = models.ManyToManyField(Sample, verbose_name='Source of Variant Associations (GWAS)', related_name='score_variants')
    samples_training = models.ManyToManyField(Sample, verbose_name='Score Development/Training', related_name='score_training')

    # Trait information
    trait_reported = models.TextField('Reported Trait')
    trait_additional = models.TextField('Additional Trait Information', null=True)
    trait_efo = models.ManyToManyField(EFOTrait, verbose_name='Mapped Trait(s) (EFO terms)', related_name='associated_scores')

    # PGS Development/method details
    method_name = models.TextField('PGS Development Method')
    method_params = models.TextField('PGS Development Details/Relevant Parameters', null=True)

    variants_number = models.IntegerField('Number of Variants', validators=[MinValueValidator(1)])
    variants_interactions = models.IntegerField('Number of Interaction Terms', default=0)
    variants_genomebuild = models.CharField('Original Genome Build', max_length=10, default='NR')

    # LICENSE information/text
    license = models.TextField('License/Terms of Use', default='''PGS obtained from the Catalog should be cited appropriately, and used in accordance with any licensing restrictions set by the authors. See EBI Terms of Use (https://www.ebi.ac.uk/about/terms-of-use/) for additional details.''')

    # Ancestry data
    ancestries = models.JSONField('Ancestry distributions', null=True)

    # Weight type
    weight_type = models.TextField('PGS Weight Type', default='NR')

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
        ftp_url = '{}/scores/{}/ScoringFiles/{}'.format(constants.USEFUL_URLS['PGS_FTP_HTTP_ROOT'], self.id, self.link_filename)
        return ftp_url

    @property
    def ftp_harmonized_scoring_files(self):
        urls = {}
        url_base_position = '{}/scores/{}/ScoringFiles/Harmonized/{}_hmPOS_'.format(constants.USEFUL_URLS['PGS_FTP_HTTP_ROOT'], self.id, self.id)
        for gb in constants.GENEBUILDS:
            urls[gb] = {}
            hm_type = 'positions'
            ftp_url = f'{url_base_position}{gb}.txt.gz'
            urls[gb][hm_type] = ftp_url
        return urls

    @property
    def list_traits(self):
        l = [] # tuples (id, label)
        for t in self.trait_efo.all():
            l.append((t.id, t.label))
        return(l)

    @property
    def has_default_license(self):
        if 'EBI Terms of Use' in self.license:
            return True
        else:
            return False


    @property
    def display_ancestry_html(self):
        ancestry_labels = constants.ANCESTRY_LABELS
        anc_stages = constants.PGS_STAGES_HELPER
        html = ''
        if self.ancestries:
            for stage in constants.PGS_STAGES:
                html_stage = ''
                if stage in self.ancestries:
                    ancestry_data = self.ancestries[stage]
                    info = f'<span class="info-icon-small" data-toggle="tooltip" data-placement="right" title="{anc_stages[stage]["desc"]}"><i class="fas fa-info-circle"></i></span>'
                    html_stage += f'<tr><td>{anc_stages[stage]["label"]}{info}</td><td>'
                    html_stage += '<div style="display:flex">'
                    chart = []
                    legend = ''
                    id = "score_anc_"+stage
                    multi_legend = {}
                    multi_anc = 'multi'
                    if multi_anc in ancestry_data:
                        for mt in ancestry_data[multi_anc]:
                            (ma,anc) = mt.split('_')
                            if ma not in multi_legend:
                                multi_legend[ma] = []
                            multi_legend[ma].append(f'<li>{ancestry_labels[anc]}</li>')

                    for key,val in sorted(ancestry_data['dist'].items(), key=lambda item: float(item[1]), reverse=True):
                        chart.append(f'"{key}",{val}')
                        label = ancestry_labels[key]
                        multi_anc_html = ''
                        if key in multi_legend:
                            multi_anc_html += f' <a class="toggle_btn pgs_btn_plus" data-toggle="tooltip" data-placement="right" data-delay="500" id="{key}_{stage}" title="" data-original-title="Click to show/hide the list of ancestries"></a></div>'
                            multi_anc_html += f'<div class="toggle_list" id="list_{key}_{stage}"><ul>{"".join(multi_legend[key])}</ul>'
                        legend += f'<div><span class="fas fa-square ancestry_box_legend anc_colour_{key}" data-key="{key}"></span>{label}: {val}%{multi_anc_html}</div>'

                    count = ancestry_data['count']
                    if count == 0:
                        html_count = ''
                    else:
                        if stage == 'eval':
                            count_data = f'{count} Sample Sets'
                        else:
                            count_data = common.individuals_format(count,1)
                            count_data = count_data.replace('</div>',' (100%)</div>')
                        html_count = f'<div class="mt-1">{count_data}</div>'
                    html_stage += f'<div class="anc_chart mr-4" data-id="'+id+'" data-chart=\'[['+'],['.join(chart)+']]\'><svg id="'+id+'"></svg></div>'
                    html_stage += '<div class="ancestry_legend">'+legend+html_count+'</div>'
                    html_stage += '</div></td></tr>'
                html += html_stage
        return html


class EvaluatedScore(models.Model):
    publication = models.ForeignKey(Publication, on_delete=models.PROTECT, verbose_name='PGS Publication ID (PGP)', related_name='publication_evaluatedscore')
    scores_evaluated = models.ManyToManyField(Score, verbose_name='Evaluated Scores', related_name='score_evaluatedscore')

    @property
    def evaluated_scores_ids(self):
        return [x.id for x in self.scores_evaluated.all().order_by('id')]


class SampleSet(models.Model):
    # Stable identifiers for declaring a set of related samples
    num = models.IntegerField('PGS Sample Set (PSS) Number', primary_key=True)
    id = models.CharField('PGS Sample Set (PSS) ID', max_length=30, db_index=True)

    name = models.CharField('Sample Set ID (curation template)', max_length=100, null=True)

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
    def samples_combined_ancestry_key(self):
        '''
        Fetch the ancestry of each sample and group them into multi-ancestry
        if there are more than one ancestry categories.
        Returns the corresponding ancestry key (2-3 letters).
        '''
        ancestry_list = []
        main_ancestry_key = ''
        for sample in self.samples.all():
            ancestry = sample.ancestry_broad.strip()
            ancestry_key = self.get_ancestry_key(ancestry)
            if ancestry_key and ancestry_key not in ancestry_list:
                ancestry_list.append(ancestry_key)

        if len(ancestry_list) > 1:
            has_eur = 0
            for anc in ancestry_list:
                if anc == 'EUR':
                    has_eur = 1
            if has_eur == 1:
                main_ancestry_key = 'MAE'
            else:
                main_ancestry_key = 'MAO'
        else:
            main_ancestry_key = ancestry_list[0]
        return main_ancestry_key

    @property
    def count_samples(self):
        return self.samples.count()

    @property
    def count_individuals(self):
        count = 0
        for sample in self.samples.all():
            if sample.sample_number:
                count += sample.sample_number
        return count

    @property
    def count_performances(self):
        return len(Performance.objects.values('id').filter(sampleset_id=self.num))


    def get_ancestry_key(self,anc):
        anc_key = 'OTH'
        if anc in constants.ANCESTRY_MAPPINGS.keys():
            anc_key = constants.ANCESTRY_MAPPINGS[anc]
        elif ',' in anc:
            if 'European' in anc:
                anc_key = 'MAE'
            else:
                anc_key = 'MAO'
        return anc_key



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
        return self.get_effect_sizes_list()


    @property
    def class_acc_list(self):
        return self.get_class_acc_list()


    @property
    def othermetrics_list(self):
        return self.get_othermetrics_list()


    @property
    def performance_metrics(self):
        perf_metrics = {}

        effect_sizes_list = self.get_effect_sizes_list(True)
        effect_sizes_data = []
        if effect_sizes_list:
            for effect_size in effect_sizes_list:
                effect_size_labels = { 'name_long': effect_size[0][0], 'name_short': effect_size[0][1] }
                effect_sizes_data.append({ **effect_size_labels, **effect_size[1] })
        perf_metrics['effect_sizes'] = effect_sizes_data

        class_acc_list = self.get_class_acc_list(True)
        class_acc_data = []
        if class_acc_list:
            for class_acc in class_acc_list:
                class_acc_labels = { 'name_long': class_acc[0][0], 'name_short': class_acc[0][1] }
                class_acc_data.append({ **class_acc_labels, **class_acc[1] })
        perf_metrics['class_acc'] = class_acc_data

        othermetrics_list = self.get_othermetrics_list(True)
        othermetrics_data = []
        if othermetrics_list:
            for othermetrics in othermetrics_list:
                othermetrics_labels = { 'name_long': othermetrics[0][0], 'name_short': othermetrics[0][1] }
                othermetrics_data.append({ **othermetrics_labels, **othermetrics[1] })
        perf_metrics['othermetrics'] = othermetrics_data

        return perf_metrics


    @property
    def publication_withexternality(self):
        """This function checks whether the evaluation is internal or external to the score development paper"""
        if self.publication.id == self.score.publication.id:
            return 'D'
        else:
            return 'E'


    def get_effect_sizes_list(self,as_dict=False):
        return self.get_metric_data('Effect Size',as_dict)


    def get_class_acc_list(self,as_dict=False):
        return self.get_metric_data('Classification Metric',as_dict)


    def get_othermetrics_list(self,as_dict=False):
        return self.get_metric_data('Other Metric',as_dict)


    def get_metric_data(self, metric_type, as_dict):
        """ Generic method to extract and format the diverse metric data"""
        # Using all and filter afterward uses less SQL queries than filtering directly on the queryset
        metrics = self.performance_metric.all()
        if metrics:
            l = []
            for m in metrics:
                if (m.type == metric_type):
                    if as_dict:
                        l.append((m.name_tuple(), m.display_values_dict()))
                    else:
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
        elif self.se != None:
            s = '{} ({})'.format(self.estimate, self.se)
        else:
            s = '{}'.format(self.estimate)

        if (self.name_short):
            return '%s (%s): %s'%(self.name, self.name_short, s)
        else:
            return '%s: %s'%(self.name, s)


    def display_value(self):
        # Use the scientific notation
        if (0 < self.estimate < 0.00001) or (-0.00001 < self.estimate < 0):
            estimate_value = '{:.2e}'.format(self.estimate)
        # Round numbers to 5 numbers max
        else:
            estimate_value = round(self.estimate, 5)
        if self.ci != None:
            s = '{} {}'.format(estimate_value, self.ci)
        elif self.se != None:
            s = '{} ({})'.format(estimate_value, self.se)
        else:
            s = '{}'.format(estimate_value)
        if self.unit != '':
            s += ' {}'.format(self.unit)
        return s


    def display_values_dict(self):
        l = {}
        l['estimate'] = self.estimate
        if self.ci != None:
            l['ci_lower'] = float(self.ci.lower)
            l['ci_upper'] = float(self.ci.upper)
        elif self.se != None:
            l['se'] = self.se
        if self.unit != '':
            l['unit'] = self.unit
        return l


    def name_tuple(self):
        if self.name_short is None:
            return (self.name, self.name)
        else:
            return (self.name, self.name_short)


class EFOTrait_Ontology(EFOTrait_Base):
    """ Class similar to the EFOTrait class, with the addition of the associated PGS Scores and
    the parents and children of the EFO trait """
    scores_direct_associations = models.ManyToManyField(Score, verbose_name='PGS Score IDs - direct associations', related_name='scores_trait_direct_associations')
    scores_child_associations = models.ManyToManyField(Score, verbose_name='PGS Score IDs - child associations', related_name='scores_trait_child_associations')

    child_traits = models.ManyToManyField('self', verbose_name='Child traits', symmetrical=False, related_name='parent_traits')

    @property
    def associated_pgs_ids(self):
        # Using 'all' and filter afterward uses less SQL queries than a direct distinct()
        score_ids_set = set(score.id for score in self.scores_direct_associations.all())
        return sorted(score_ids_set)

    @property
    def child_associated_pgs_ids(self):
        # Using 'all' and filter afterward uses less SQL queries than a direct distinct()
        score_ids_set = set(score.id for score in self.scores_child_associations.all())
        return sorted(score_ids_set)

    @property
    def display_child_traits_list(self):
        child_traits = self.child_traits.all()
        if child_traits:
            child_traits_list = []
            for child_trait in sorted(child_traits, key=lambda y: y.label):
                child_trait_html = '<a href="/trait/{}">{}</a>'.format(child_trait.id, child_trait.label)
                child_traits_list.append(child_trait_html)
            return child_traits_list
        else:
            return []


class TraitCategory(models.Model):
    """ Class to hold information about Trait category, as defined by the GWAS Catalog, to structure the numerous traits in broad groups."""
    # Stable identifiers for declaring a set of traits
    label = models.CharField('Trait category', max_length=50, db_index=True)
    colour = models.CharField('Trait category colour', max_length=30)
    parent = models.CharField('Trait category (parent term)', max_length=50)

    # Link to the list of associated EFOTrait models
    efotraits = models.ManyToManyField(EFOTrait, verbose_name='Traits', related_name='traitcategory')

    # Link to the list of associated EFOTrait_Ontology models
    efotraits_ontology = models.ManyToManyField(EFOTrait_Ontology, verbose_name='Parent Traits', related_name='traitcategory')

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


class EmbargoedPublication(models.Model):
    """Class to store the list of embargoed Publications"""
    # Stable identifier
    id = models.CharField('PGS Publication/Study ID (PGP)', max_length=30, primary_key=True)
    title = models.TextField('Title', null=True)
    firstauthor = models.CharField('First Author', max_length=50)


class EmbargoedScore(models.Model):
    """Class to store the list of embargoed Scores"""
    # Stable identifier
    id = models.CharField('Polygenic Score ID', max_length=30, primary_key=True)
    name = models.CharField('PGS Name', max_length=100)
    trait_reported = models.TextField('Reported Trait')
    firstauthor = models.CharField('First Author', max_length=50)


class Retired(models.Model):
    """Class to store the list of retired Scores/Publications"""
    # Stable identifier
    id = models.CharField('Score or Publication ID', max_length=30, primary_key=True)
    doi = models.CharField('digital object identifier (doi)', max_length=100)
    notes = models.TextField(verbose_name='Retirement notes', max_length=600, blank=True)


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
        scores = Score.objects.values_list('id', flat=True).filter(date_released__exact=self.date).order_by('id')
        return list(scores)

    @property
    def released_publication_ids(self):
        publications = Publication.objects.values_list('id', flat=True).filter(date_released__exact=self.date).order_by('id')
        return list(publications)

    @property
    def released_performance_ids(self):
        performances = Performance.objects.values_list('id', flat=True).filter(date_released__exact=self.date).order_by('id')
        return list(performances)
