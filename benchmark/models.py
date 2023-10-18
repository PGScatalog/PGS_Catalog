from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.postgres.fields import DecimalRangeField


class BM_Coding(models.Model):
    """Class to describe the International Classification of Diseases used in PGS """
    id = models.CharField('Code ID', max_length=30, primary_key=True)
    label = models.CharField('Code Label', max_length=500, db_index=True)
    type = models.CharField('Code Type', max_length=10)


class BM_Cohort(models.Model):
    """Class to describe cohorts used in samples"""
    name_short = models.CharField('Cohort Short Name', max_length=100, db_index=True)
    name_full = models.CharField('Cohort Full Name', max_length=1000)

    def __str__(self):
        return self.name_short


class BM_EFOTrait(models.Model):
    """Abstract class to hold information related to controlled trait vocabulary
    (mainly to link multiple EFO to a single score)"""
    id = models.CharField('Ontology Trait ID', max_length=30, primary_key=True)
    label = models.CharField('Ontology Trait Label', max_length=500, db_index=True)
    description = models.TextField('Ontology Trait Description', null=True)
    #url = models.CharField('Ontology URL', max_length=500)
    #synonyms = models.TextField('Synonyms', null=True)
    #mapped_terms = models.TextField('Mapped terms', null=True)
    phenotype_structured = models.ManyToManyField(BM_Coding, verbose_name='Codings', related_name='coding_trait')

    def __str__(self):
        return '%s | %s '%(self.id, self.label)

    @property
    def display_label(self):
        return '<a href="/benchmark/%s">%s</a>'%(self.id, self.label)

    #@property
    #def display_id_url(self):
    #    return '<a href="%s">%s</a><span class="only_export">: %s</span>'%(self.url, self.id, self.url)


    @property
    def display_phenotype_structured(self):
        data = []
        phenotype_structured = self.phenotype_structured.all()
        for phenotype in self.phenotype_structured.all():
            data.append('<b>'+phenotype.id+'</b>: '+phenotype.label)
        return data


    def get_bm_data(self):
        self.bm_data = {}
        data_types = ['scores', 'cohorts', 'samples', 'ancestries']
        data = {}
        for type in data_types:
            data[type] = set()

        for bm_performance in self.efotrait_performance.all():
            data['scores'].add(bm_performance.score_id)
            data['cohorts'].add(bm_performance.cohort)
            data['samples'].add(bm_performance.sample.id)
            data['ancestries'].add(bm_performance.sample.ancestry_broad)

        for type in data_types:
            self.bm_data[type] = list(data[type])

    @property
    def count_scores(self):
        if not hasattr(self, 'bm_data'):
            self.get_bm_data()
        return len(self.bm_data['scores'])

    @property
    def count_cohorts(self):
        if not hasattr(self, 'bm_data'):
            self.get_bm_data()
        return len(self.bm_data['cohorts'])

    @property
    def count_samples(self):
        if not hasattr(self, 'bm_data'):
            self.get_bm_data()
        return len(self.bm_data['samples'])

    @property
    def cohorts_list(self):
        if not hasattr(self, 'bm_data'):
            self.get_bm_data()
        return self.bm_data['cohorts']

    @property
    def ancestries_list(self):
        if not hasattr(self, 'bm_data'):
            self.get_bm_data()
        return self.bm_data['ancestries']


class BM_Demographic(models.Model):
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


class BM_Sample(models.Model):
    """Class to describe samples used in variant associations and PGS training/testing"""

    # Sample Information
    ## Numbers
    sample_number = models.IntegerField('Number of Individuals', validators=[MinValueValidator(1)])
    sample_cases = models.IntegerField('Number of Cases', null=True)
    sample_controls = models.IntegerField('Number of Controls', null=True)
    # Sample sex type information
    SAMPLE_SEX_CHOICES = [
        ('Both', 'Both'),
        ('Male', 'Male'),
        ('Female', 'Female')
    ]
    sample_sex = models.CharField(max_length=6,
                            choices=SAMPLE_SEX_CHOICES,
                            default='Both',
                            verbose_name='Sample Sex'
                        )
    sample_age = models.OneToOneField(BM_Demographic, on_delete=models.CASCADE,related_name='ages_of', null=True)

    ## Description
    phenotyping_free = models.TextField('Detailed Phenotype Description', null=True)
    phenotype_structured = models.ManyToManyField(BM_Coding, verbose_name='Codings', related_name='coding_sample')

    followup_time = models.OneToOneField(BM_Demographic, on_delete=models.CASCADE,related_name='followuptime_of', null=True)

    ## Ancestry
    ancestry_broad = models.CharField('Broad Ancestry Category', max_length=100)
    ancestry_free = models.TextField('Ancestry (e.g. French, Chinese)', null=True)
    ancestry_country = models.TextField('Country of Recruitment', null=True)
    ancestry_additional = models.TextField('Additional Ancestry Description', null=True)

    ## Cohorts/Sources
    cohort = models.ForeignKey(BM_Cohort, verbose_name='Cohort', on_delete=models.PROTECT, related_name='cohort_sample')
    
    def __str__(self):
        return 'Sample: {}'.format(str(self.pk))

    @property
    def sample_cases_percent(self):
        if self.sample_cases != None:
            percent = (self.sample_cases / self.sample_number) * 100
            return round(percent,2)
        else:
            return None

    def display_samples_for_table(self, show_percent_cases=False):
        div_id = "sample_"+str(self.pk)
        sstring = ''
        if self.sample_cases != None:
            percent_cases = ''
            if show_percent_cases:
                percent_cases = f' ({self.sample_cases_percent}%)'
            sstring += '<div><a class="toggle_table_btn pgs_btn_plus pgs_helptip" id="'+div_id+'" title="Click to show/hide the details">{:,} individuals</a></div>'.format(self.sample_number)
            sstring += '<div class="toggle_list" id="list_'+div_id+'">'
            sstring += '<span class="only_export">[</span>'
            sstring += '<ul>\n<li>{:,} cases{}</li>\n'.format(self.sample_cases, percent_cases)
            if self.sample_controls != None:
                sstring += '<li><span class="only_export">, </span>'
                sstring += '{:,} controls</li>'.format(self.sample_controls)
            sstring += '</ul>'
            sstring += '<span class="only_export">]</span>'
            sstring += '</div>'
        else:
            sstring += '{:,} individuals'.format(self.sample_number)
        return sstring

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


class BM_Performance(models.Model):
    """Class to hold performance/accuracy metrics for a PGS and a set of samples"""

    # Links to related objects
    score_id = models.CharField('Polygenic Score (PGS) ID', max_length=30, db_index=True)

    sample = models.ForeignKey(BM_Sample, on_delete=models.PROTECT, verbose_name='PGS Sample',
                                    related_name='sample_performance') # Samples used for evaluation

    efotrait = models.ForeignKey(BM_EFOTrait, on_delete=models.PROTECT, verbose_name='EFO Trait', related_name="efotrait_performance")

    cohort = models.ForeignKey(BM_Cohort, verbose_name='Cohort', on_delete=models.PROTECT, related_name='cohort_performance')

    def __str__(self):
        return '%s | %s | %s'%(self.efotrait.id, self.score_id, self.cohort.name_short)

    class Meta:
        get_latest_by = 'num'

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


class BM_Metric(models.Model):
    """Class to hold metric type, name, value and confidence intervals of a performance metric"""
    performance = models.ForeignKey(BM_Performance, on_delete=models.CASCADE, verbose_name='PGS Performance Metric (PPM)', related_name="performance_metric")

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
    name_short = models.CharField(verbose_name='Performance Metric Name (Short)', max_length=25, null=True) # ex: "OR"

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
