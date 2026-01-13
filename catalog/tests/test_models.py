from django.test import TestCase
import datetime as dt
from psycopg.types.range import NumericRange
from pgs_web import constants
from catalog.models import *

test_sample_number = 5
test_sample_count  = 7

default_num = 1

efo_id = 'EFO_0000305'
efo_id_colon = efo_id.replace('_',':')
efo_name = 'breast carcinoma'
efo_desc_list = ['A carcinoma that arises from epithelial cells of the breast']
efo_desc = ' | '.join(efo_desc_list)
efo_synonyms_list = ['CA - Carcinoma of breast','Carcinoma of breast NOS','Mammary Carcinoma, Human']
efo_synonyms = ' | '.join(efo_synonyms_list)
efo_mapped_terms_list = ['OMIM:615554','NCIT:C4872','UMLS:C0678222']
efo_mapped_terms = ' | '.join(efo_mapped_terms_list)

efo_id_2   = 'EFO_1000649'
efo_name_2 = 'estrogen-receptor positive breast cancer'
efo_desc_2 = 'a subtype of breast cancer that is estrogen-receptor positive [EFO: 1000649]'

cohort_name = "ABC"
cohort_desc = "Cohort ABC description"
cohort_others = "ABC-1"
cohort_name_2 = "DEF"
cohort_desc_2 = "Cohort DEF description"

firstauthor = "Inouye M"


def format_date(date_list):
    return dt.date(int(date_list[0]),int(date_list[1]),int(date_list[2]))


class CohortTest(TestCase):
    ''' Test the Cohort model '''

    def create_cohort(self, name_short=cohort_name,name_full=cohort_desc,name_others=cohort_others):
        return Cohort.objects.create(name_short=name_short,name_full=name_full,name_others=name_others)

    def get_cohort(self,name_short,name_full,name_others):
        try:
            cohort = Cohort.objects.get(name_short=name_short)
        except Cohort.DoesNotExist:
            cohort = self.create_cohort(name_short=name_short,name_full=name_full,name_others=name_others)
        return cohort

    def test_cohort(self):
        cohort= self.get_cohort(cohort_name,cohort_desc,cohort_others)
        # Instance
        self.assertTrue(isinstance(cohort, Cohort))
        # Variables
        self.assertEqual(cohort.name_short, cohort_name)
        self.assertEqual(cohort.name_full, cohort_desc)
        self.assertEqual(cohort.name_others, cohort_others)
        # Other methods
        self.assertEqual(cohort.__str__(), cohort.name_short)
        self.assertFalse(cohort.released)
        cohort.released = True
        cohort.save()
        self.assertTrue(cohort.released)

class DemographicTest(TestCase):
    ''' Test the Demographic model '''

    def create_demographic(self, estimate, estimate_type, unit, range, range_type, variability, variability_type):
        return Demographic.objects.create(
            estimate=estimate,
            estimate_type=estimate_type,
            unit=unit,
            range=range,
            range_type=range_type,
            variability=variability,
            variability_type=variability_type
        )


    def test_demographic_a(self):
        ''' Type "median" - no variability '''
        a_type = 'median'
        a_estimate = 10
        a_unit = 'years'
        a_range_lower = 0.0
        a_range_upper = 20.0
        a_range_string = f'[{a_range_lower}, {a_range_upper}]'
        a_range = NumericRange(lower=a_range_lower, upper=a_range_upper, bounds='[]')
        a_range_type = 'range'
        a_variability = None
        a_variability_type = 'se'
        demographic_a = self.create_demographic(a_estimate,a_type,a_unit,a_range,a_range_type,a_variability,a_variability_type)
        # Instance
        self.assertTrue(isinstance(demographic_a, Demographic))
        # Variables
        self.assertEqual(demographic_a.estimate,a_estimate)
        self.assertEqual(demographic_a.estimate_type,a_type)
        self.assertEqual(demographic_a.unit,a_unit)
        self.assertEqual(demographic_a.range,a_range)
        self.assertEqual(demographic_a.range_type,a_range_type)
        self.assertEqual(demographic_a.variability,a_variability)
        self.assertEqual(demographic_a.variability_type,a_variability_type)
        # Other methods
        self.assertEqual(demographic_a.format_estimate(), a_type+':'+str(a_estimate))
        self.assertIsNone(demographic_a.format_range())
        self.assertIsNone(demographic_a.format_variability())
        self.assertEqual(demographic_a.format_unit(),'unit:'+a_unit)
        self.assertEqual(demographic_a.variability_type_desc(), 'Standard Error')
        regex_range_a = a_range_string.replace('[','\[').replace(']','\]')
        demo_value_a =  r'^<ul><li>'+a_type.title()+r' : '+str(a_estimate)+r' '+a_unit
        demo_value_a += r'</li><li>'+a_range_type.title()+r' : '+regex_range_a+r' '+a_unit+r'.+$'
        self.assertRegex(demographic_a.display_value(), demo_value_a)
        values_dict_a = demographic_a.display_values_dict()
        self.assertEqual(values_dict_a['estimate_type'], a_type)
        self.assertEqual(values_dict_a['estimate'], a_estimate)
        self.assertEqual(values_dict_a['interval']['type'], a_range_type)
        self.assertEqual(values_dict_a['interval']['lower'], a_range_lower)
        self.assertEqual(values_dict_a['interval']['upper'], a_range_upper)
        self.assertEqual(values_dict_a['unit'], a_unit)


    def test_demographic_b(self):
        ''' Type "mean" - no range '''
        b_type = 'mean'
        b_estimate = 6.3
        b_unit = 'years'
        b_range = None
        b_range_type = 'range'
        b_variability = 1.9
        b_variability_type = 'sd'
        demographic_b = self.create_demographic(b_estimate,b_type,b_unit,b_range,b_range_type,b_variability,b_variability_type)
        # Instance
        self.assertTrue(isinstance(demographic_b, Demographic))
        # Other methods
        self.assertIsNone(demographic_b.format_range())
        self.assertEqual(demographic_b.format_variability(), '{}:{}'.format(b_variability_type,b_variability))
        demo_value_b =  r'^<ul><li>'+b_type.title()+r' : '+str(b_estimate)+r' '+b_unit
        demo_value_b += r'</li><li><span.+>'+b_variability_type.title()+r'</span> : '+str(b_variability)+r' '+b_unit+r'.+$'
        self.assertRegex(demographic_b.display_value(), demo_value_b)
        values_dict_b = demographic_b.display_values_dict()
        self.assertEqual(values_dict_b['variability_type'], b_variability_type)
        self.assertEqual(values_dict_b['variability'], b_variability)


    def test_demographic_c(self):
        ''' Type "mean" - no variability '''
        c_type = 'mean'
        c_estimate = 11.1
        c_unit = 'years'
        c_range_lower = 10.0
        c_range_upper = 12.0
        c_range_string = f'[{c_range_lower}, {c_range_upper}]'
        c_range = NumericRange(lower=c_range_lower, upper=c_range_upper, bounds='[]')
        c_range_type = 'iqr'
        c_variability = None
        c_variability_type = 'se'
        demographic_c = self.create_demographic(c_estimate,c_type,c_unit,c_range,c_range_type,c_variability,c_variability_type)
        # Instance
        self.assertTrue(isinstance(demographic_c, Demographic))
        # Variables
        self.assertEqual(demographic_c.estimate_type,c_type)
        # Other methods
        self.assertEqual(demographic_c.range_type_desc(), 'Interquartile range')
        regex_range_c = c_range_string.replace('[','\[').replace(']','\]')
        demo_value_c =  r'^<ul><li>'+c_type.title()+r' : '+str(c_estimate)+r' '+c_unit
        demo_value_c += r'</li><li><span.+>'+c_range_type.title()+r'</span> : '+regex_range_c+r' '+c_unit+r'.+$'
        self.assertRegex(demographic_c.display_value(), demo_value_c)


    def test_demographic_d(self):
        ''' Type "mean" - no estimate '''
        d_type = 'mean'
        d_estimate = None
        d_unit = 'years'
        d_range = '[50.0,69.0]'
        d_range_type = 'range'
        d_variability = None
        d_variability_type = 'se'
        demographic_d = self.create_demographic(d_estimate,d_type,d_unit,d_range,d_range_type,d_variability,d_variability_type)
        # Instance
        self.assertTrue(isinstance(demographic_d, Demographic))
        # Other methods
        self.assertIsNone(demographic_d.format_estimate())
        self.assertEqual(demographic_d.format_range(),d_range_type+':'+d_range)
        regex_range_d = d_range.replace('[','\[').replace(']','\]')
        demo_value_d =  r'^'+d_range_type.title()+r' : '+regex_range_d+r' '+d_unit+r'$'
        self.assertRegex(demographic_d.display_value(), demo_value_d)


    def test_demographic_e(self):
        ''' Type "median" - ci range, no unit '''
        e_type = 'median'
        e_estimate = 15
        e_unit =  'years'
        e_range_lower = 12
        e_range_upper = 17
        e_range_string = f'[{e_range_lower}, {e_range_upper}]'
        e_range = NumericRange(lower=e_range_lower, upper=e_range_upper, bounds='[]')
        e_range_type = 'ci'
        e_variability = 1.2
        e_variability_type = 'Test'
        demographic_e = self.create_demographic(e_estimate,e_type,e_unit,e_range,e_range_type,e_variability,e_variability_type)
        # Instance
        self.assertTrue(isinstance(demographic_e, Demographic))
        # Other methods
        regex_range_e = e_range_string.replace('[','\[').replace(']','\]')
        demo_value_e =  r'^<ul><li>'+e_type.title()+r' : '+str(e_estimate)+r' '+regex_range_e+r' '+e_unit
        demo_value_e += r'</li><li>'+e_variability_type.title()+r' : '+str(e_variability)+r' '+e_unit+r'</li></ul>$'
        self.assertRegex(demographic_e.display_value(), demo_value_e)
        values_dict_e = demographic_e.display_values_dict()
        self.assertEqual(values_dict_e['estimate'], f'{e_estimate} {e_range_string}')


class EFOTraitTest(TestCase):
    ''' Test the EFOTrait model '''

    def create_efo_trait(self, efo_id=efo_id,label=efo_name, desc=efo_desc, syn=efo_synonyms, terms=efo_mapped_terms):
        return EFOTrait.objects.create(id=efo_id,label=label,description=desc,synonyms=syn,mapped_terms=terms)

    def get_efo_trait(self, efo_trait_id, efo_trait_label, efo_trait_desc):
        try:
            efo_trait = EFOTrait.objects.get(id=efo_trait_id)
        except EFOTrait.DoesNotExist:
            efo_trait = self.create_efo_trait(efo_id=efo_trait_id,label=efo_trait_label, desc=efo_trait_desc)
        return efo_trait


    def test_efo_trait_1(self):
        efo_trait_1 = self.get_efo_trait(efo_id,efo_name,efo_desc)
        # Instance
        self.assertTrue(isinstance(efo_trait_1, EFOTrait))
        # Variables
        self.assertIsNotNone(efo_trait_1.label)
        self.assertIsNotNone(efo_trait_1.url)
        self.assertIsNotNone(efo_trait_1.description)
        self.assertEqual(efo_trait_1.id, efo_id)
        self.assertEqual(efo_trait_1.id_colon, efo_id_colon)
        self.assertEqual(efo_trait_1.label, efo_name)
        self.assertEqual(efo_trait_1.description, efo_desc)
        self.assertEqual(efo_trait_1.description_list, efo_desc_list)
        self.assertEqual(efo_trait_1.synonyms, efo_synonyms)
        self.assertEqual(efo_trait_1.mapped_terms, efo_mapped_terms)
        self.assertEqual(efo_trait_1.synonyms_list, efo_synonyms_list)
        self.assertEqual(efo_trait_1.mapped_terms_list, efo_mapped_terms_list)
        # Other methods
        self.assertEqual(efo_trait_1.__str__(), efo_id+' | '+efo_name+' ')
        label_url =  r'^\<a\s.*href=.+\/trait\/'+efo_id+r'.*\>'+efo_name+r'\<\/a\>$'
        self.assertRegex(efo_trait_1.display_label, label_url)
        id_url = r'^\<a\s.*href=.+\>'+efo_id+r'\<\/a\>$'
        self.assertRegex(efo_trait_1.display_ext_url, id_url)
        efo_trait_1.parse_api()
        self.assertEqual(efo_trait_1.label, efo_name)
        self.assertTrue(efo_trait_1.description.startswith(efo_desc))
        self.assertIsNotNone(efo_trait_1.url)
        self.assertEqual(efo_trait_1.category_labels_list, [])


    def test_efo_trait_2(self):
        ''' Test empty synonyms & mapped_terms '''
        efo_trait_2 = self.create_efo_trait(efo_id='EFO_0000306', syn=None, terms=None)
        # Instance
        self.assertTrue(isinstance(efo_trait_2, EFOTrait))
        # Other methods
        self.assertEqual(efo_trait_2.synonyms_list, [])
        self.assertEqual(efo_trait_2.mapped_terms_list, [])


class MetricTest(TestCase):
    ''' Test the Metric model '''

    def create_performance(self, num):
        performancetest = PerformanceTest()
        performance = performancetest.get_performance(num)
        return performance

    def create_metric(self, performance_id, type, name, name_short, estimate, unit, se, ci):

        return Metric.objects.create(
            performance_id=performance_id,
            type=type,
            name=name,
            name_short=name_short,
            estimate=estimate,
            unit=unit,
            se=se,
            ci=ci
        )

    def test_metric(self):
        # Create Performance object
        performancetest = PerformanceTest()
        performance = performancetest.get_performance(default_num)

        # Type "Effect size"
        e_type = 'Effect Size'
        e_name = 'Beta'
        e_name_short = 'β'
        e_estimate = -0.7
        e_estimate_2 = 0.0123456789
        e_estimate_2_rounded = 0.01235
        e_estimate_3 = 0.00000231
        e_estimate_3_rounded = 2.31e-6
        e_estimate_4 = -0.0000003423
        e_estimate_4_rounded = -3.42e-7
        e_estimate_5 = 1.24674178
        e_estimate_5_rounded = 1.24674
        e_unit = 'years'

        metric_effect = self.create_metric(performance.num,e_type,e_name,e_name_short,e_estimate,e_unit,None,None)
        # Instance
        self.assertTrue(isinstance(metric_effect, Metric))
        # Other methods
        self.assertEqual(metric_effect.display_value(),f'{e_estimate} {e_unit}')
        self.assertEqual(metric_effect.name_tuple(), (e_name,e_name_short))
        self.assertEqual(metric_effect.__str__(), f'{e_name} ({e_name_short}): {e_estimate}')

        metric_effect.estimate = e_estimate_2
        self.assertEqual(metric_effect.display_value(),f'{e_estimate_2_rounded} {e_unit}')

        metric_effect.estimate = e_estimate_3
        self.assertEqual(metric_effect.display_value(),f'{e_estimate_3_rounded} {e_unit}')

        metric_effect.estimate = e_estimate_4
        self.assertEqual(metric_effect.display_value(),f'{e_estimate_4_rounded} {e_unit}')

        metric_effect.estimate = e_estimate_5
        metric_effect.unit = ''
        self.assertEqual(metric_effect.display_value(),f'{e_estimate_5_rounded}')

        # Test Standard error
        s_estimate = 0.123
        s_standard_error = 0.021
        metric_effect.estimate = s_estimate
        metric_effect.se = s_standard_error
        metric_effect.save()
        self.assertEqual(metric_effect.__str__(), f'{e_name} ({e_name_short}): {s_estimate} ({s_standard_error})')
        self.assertEqual(metric_effect.display_value(),f'{s_estimate} ({s_standard_error})')
        s_metrics_dict = metric_effect.display_values_dict()
        self.assertEqual(s_metrics_dict['estimate'], s_estimate)
        self.assertEqual(s_metrics_dict['se'], s_standard_error)


        # Type "Classification Metric"
        c_type = 'Classification Metric'
        c_name = 'Concordance Statistic'
        c_name_short = 'C-index'
        c_estimate = 0.655
        c_ci_lower = 0.605
        c_ci_upper = 0.667
        c_ci_string = f'[{c_ci_lower}, {c_ci_upper}]'
        c_ci = NumericRange(lower=c_ci_lower, upper=c_ci_upper, bounds='[]')
        metric_class = self.create_metric(performance.num,c_type,c_name,c_name_short,c_estimate,'',None,c_ci)
        # Instance
        self.assertTrue(isinstance(metric_class, Metric))
        # Other methods
        self.assertEqual(metric_class.display_value(), f'{c_estimate} {c_ci_string}')
        self.assertEqual(metric_class.name_tuple(), (c_name,c_name_short))
        self.assertEqual(metric_class.__str__(), f'{c_name} ({c_name_short}): {c_estimate} {c_ci_string}')
        c_metrics_dict = metric_class.display_values_dict()
        self.assertEqual(c_metrics_dict['estimate'], c_estimate)
        self.assertEqual(c_metrics_dict['ci_lower'], c_ci_lower)
        self.assertEqual(c_metrics_dict['ci_upper'], c_ci_upper)


        # Type "Other Metric"
        o_type = 'Other Metric'
        o_name = 'correlation (r)'
        o_name_short = None
        o_estimate = 0.29
        o_ci_lower = 0.231
        o_ci_upper = 0.349
        o_ci_string = f'[{o_ci_lower}, {o_ci_upper}]'
        o_ci = NumericRange(lower=o_ci_lower, upper=o_ci_upper, bounds='[]')
        metric_other = self.create_metric(performance.num,o_type,o_name,o_name_short,o_estimate,'',None,o_ci)
        # Instance
        self.assertTrue(isinstance(metric_other, Metric))
        # Other methods
        self.assertEqual(metric_other.display_value(), str(o_estimate)+' '+o_ci_string)
        self.assertEqual(metric_other.name_tuple(), (o_name,o_name))
        self.assertEqual(metric_other.__str__(), f'{o_name}: {o_estimate} {o_ci_string}')
        o_metrics_dict = metric_other.display_values_dict()
        self.assertEqual(o_metrics_dict['estimate'], o_estimate)
        self.assertEqual(o_metrics_dict['ci_lower'], o_ci_lower)
        self.assertEqual(o_metrics_dict['ci_upper'], o_ci_upper)

        # Performance tests
        perf_effect = performance.effect_sizes_list
        self.assertEqual(len(perf_effect), 1)
        self.assertEqual(perf_effect[0][0][0], e_name)

        perf_class = performance.class_acc_list
        self.assertEqual(len(perf_class), 1)
        self.assertEqual(perf_class[0][0][0], c_name)

        perf_other = performance.othermetrics_list
        self.assertEqual(len(perf_other), 1)
        self.assertEqual(perf_other[0][0][0], o_name)

        perf_dict = performance.performance_metrics
        self.assertEqual(perf_dict['effect_sizes'], [{ 'name_long': e_name, 'name_short': e_name_short, **s_metrics_dict }])
        c_value = metric_class.display_value().replace(',', ', ')
        self.assertEqual(perf_dict['class_acc'], [{ 'name_long': c_name, 'name_short': c_name_short, **c_metrics_dict }])
        o_value = metric_other.display_value().replace(',', ', ')
        self.assertEqual(perf_dict['othermetrics'], [{ 'name_long': o_name, 'name_short': o_name, **o_metrics_dict }])


class PerformanceTest(TestCase):
    ''' Test the Performance model '''
    perf_id = 'PPM000001'
    phenotype_reported = 'New reported phenotype'

    def create_performance(self, num):
        # Score
        scoretest = ScoreTest()
        score = scoretest.get_score(default_num)

        # Publication
        pubtest = PublicationTest()
        pub = pubtest.get_publication_doi(default_num+2)

        # Sample Set
        extra_num = num
        samplesettest = SampleSetTest()
        sampleset = samplesettest.create_sampleset(num=extra_num)

        performance = Performance.objects.create(num=num, score=score, publication=pub, sampleset=sampleset)

        # EFO trait
        efotraittest = EFOTraitTest()
        efotrait = efotraittest.get_efo_trait(efo_id, efo_name, efo_desc)
        performance.phenotyping_efo.add(efotrait)

        performance.set_performance_id(num)

        performance.phenotyping_reported = self.phenotype_reported

        return performance

    def get_performance(self, num_id):
        try:
            performance = Performance.objects.get(num=num_id)
        except Performance.DoesNotExist:
            performance = self.create_performance(num_id)
        return performance

    def test_performance(self):
        id = 1

        performance = self.get_performance(id)

        es_test = EvaluatedScoreTest()
        evaluated_score = es_test.create_evaluatedscore(performance.publication,[performance.score])

        # Instance
        self.assertTrue(isinstance(performance, Performance))
        # Variables
        self.assertEqual(performance.id, self.perf_id)
        self.assertEqual(len(performance.samples()), test_sample_count)
        # Other methods
        self.assertRegex(performance.__str__(), r'^'+self.perf_id+r' \| PGS\d+ -> PSS\d+$')
        self.assertEqual(performance.publication_withexternality, 'E')
        sampleset = performance.sampleset
        self.assertEqual(sampleset.count_performances, 1)
        self.assertEqual(performance.display_trait['efo'][0], performance.phenotyping_efo.all()[0])
        self.assertEqual(performance.display_trait['reported'], self.phenotype_reported)
        self.assertTrue(isinstance(performance.publication, Publication))
        self.assertEqual(list(performance.publication.scores_evaluated), [performance.score.id])
        self.assertEqual(performance.publication.scores_evaluated_count, 1)
        self.assertEqual(performance.associated_pgs_id, performance.score.id)
        cohorttest = CohortTest()
        cohort = cohorttest.get_cohort(cohort_name,cohort_desc,cohort_others)
        sampleset.samples.all()[0].cohorts.add(cohort)
        self.assertEqual(cohort.associated_pgs_ids, { 'development': [], 'evaluation': [performance.score.id] })

        id = 2000
        performance_2 = self.get_performance(id)
        # Instance
        self.assertTrue(isinstance(performance_2, Performance))
        # Other methods
        pubtest = PublicationTest()
        pub = pubtest.create_publication_by_pmid(num=id+10)
        performance_2.publication = pub
        performance_2.score.publication = pub
        self.assertEqual(performance_2.publication_withexternality, 'D')


class PublicationTest(TestCase):
    ''' Test the Publication model '''
    first_author = "Smith J"

    def create_publication_by_doi(self, num, date="2018-10-01", id="10.1016/j.jacc.2018.07.079",author=first_author,journal='bioRxiv'):
        date_list = date.split('-')
        date_formated = format_date(date_list)
        pub = Publication.objects.create(num=num, date_publication=date_formated, doi=id, firstauthor=author, journal=journal)
        pub.set_publication_ids(num)
        return pub

    def create_publication_by_pmid(self, num, date="2015-04-08", id=25855707, journal="Lancet"):
        date_list = date.split('-')
        date_formated = format_date(date_list)
        pub = Publication.objects.create(num=num, date_publication=date_formated, PMID=id, journal=journal)
        pub.set_publication_ids(num)
        return pub

    def get_publication_doi(self, num_id):
        try:
            publication = Publication.objects.get(num=num_id)
        except Publication.DoesNotExist:
            publication = self.create_publication_by_doi(num_id)
        return publication


    def test_publication(self):
        pub_doi = self.get_publication_doi(default_num)
        # Instance
        self.assertTrue(isinstance(pub_doi, Publication))
        # Variables
        self.assertEqual(pub_doi.id, 'PGP000001')
        self.assertEqual(pub_doi.pub_year, '2018')
        # Other methods
        self.assertFalse(pub_doi.is_published())
        self.assertEqual(pub_doi.__str__(), pub_doi.id+' | '+self.first_author)
        self.assertTrue(pub_doi.is_preprint)
        pub_doi.parse_EuropePMC(doi=pub_doi.doi)
        self.assertEqual(pub_doi.PMID, '30309464')

        pub_pmid = self.create_publication_by_pmid(default_num+1)
        # Instance
        self.assertTrue(isinstance(pub_pmid, Publication))
        # Variables
        self.assertEqual(pub_pmid.id, 'PGP000002')
        self.assertEqual(pub_pmid.pub_year, '2015')
        # Other methods
        self.assertTrue(pub_pmid.is_published())
        pmid = str(pub_pmid.PMID)
        self.assertFalse(pub_pmid.is_preprint)
        pub_pmid.parse_EuropePMC(PMID=pub_pmid.PMID)
        self.assertEqual(pub_pmid.PMID, pmid)


class ReleaseTest(TestCase):
    ''' Test the Release model '''

    date_list = ['2020','03','20']
    date_string = '-'.join(date_list)
    date_formated = format_date(date_list)
    notes = "Test release"

    def create_release(self, date=date_formated,notes=notes,s_count=0,perf_count=0,pub_count=0):
        return Release.objects.create(
            date=date,
            notes=notes,
            score_count=s_count,
            performance_count=perf_count,
            publication_count=pub_count
        )

    def test_release(self):

        ids_list = { 'score':[], 'perf':[], 'pub':[] }
        # Scores
        # - Score 1
        scoretest = ScoreTest()
        score1 = scoretest.get_score(default_num)
        score1.date_released = self.date_formated
        score1.save()
        ids_list['score'].append(score1.id)
        # - Score 2
        score2 = scoretest.get_score(default_num+1)
        score2.date_released = self.date_formated
        score2.save()
        ids_list['score'].append(score2.id)

        # Performance
        perftest = PerformanceTest()
        perf = perftest.get_performance(default_num)
        perf.date_released = self.date_formated
        perf.save()
        ids_list['perf'].append(perf.id)

        # Publications
        pubtest = PublicationTest()
        pub = pubtest.get_publication_doi(default_num)
        pub.date_released = self.date_formated
        pub.save()
        ids_list['pub'].append(pub.id)

        counts = { 'score': 2, 'perf': 1, 'pub': 1 }
        release = self.create_release(s_count=counts['score'],perf_count=counts['perf'],pub_count=counts['pub'])
        # Instance
        self.assertTrue(isinstance(release, Release))
        # Variables
        self.assertEqual(release.date, self.date_formated)
        self.assertEqual(release.score_count, counts['score'])
        self.assertEqual(release.performance_count, counts['perf'])
        self.assertEqual(release.publication_count, counts['pub'])
        # Other methods
        self.assertEqual(release.released_score_ids, ids_list['score'])
        self.assertEqual(release.released_performance_ids, ids_list['perf'])
        self.assertEqual(release.released_publication_ids, ids_list['pub'])
        self.assertEqual(release.__str__(), self.date_string)


class SampleTest(TestCase):
    ''' Test the Sample model '''
    number = 10
    cases = 6
    controls = 4
    male = 40
    a_broad = 'European'
    a_free = 'NR'
    a_free_2 = 'Cambridgeshire'
    a_country = 'France, Germany, Netherlands, Estonia, Finland, Sweden, U.K., NR, U.S.'
    a_additional = 'White European'
    gwas_id = 'GCST001937'
    pmid = 23535729
    doi = '10.1038/s41588-021-00783-5'

    def get_sample(self,sample_number):
        try:
            sample = Sample.objects.get(sample_number=sample_number)
        except Sample.DoesNotExist:
            sample = self.create_sample(sample_number=sample_number)
        return sample

    def create_sample(self, sample_number=number):
        return Sample.objects.create(sample_number=sample_number)

    def create_sample_numbers(self, sample_number=number,sample_cases=cases,sample_controls=controls,sample_percent_male=male):
        return Sample.objects.create(sample_number=sample_number,sample_cases=sample_cases,sample_controls=sample_controls,sample_percent_male=sample_percent_male)

    def create_sample_ancestry(self, sample_number=number,broad=a_broad,free=a_free,country=a_country,additional=a_additional):
        return Sample.objects.create(
            sample_number=sample_number,
            ancestry_broad=broad,
            ancestry_free=free,
            ancestry_country=country,
            ancestry_additional=additional
        )

    def create_sample_cohorts(self, sample_number=number):
        sample = Sample.objects.create(sample_number=sample_number)
        cohorttest = CohortTest()
        cohort = cohorttest.get_cohort(cohort_name,cohort_desc,cohort_others)
        sample.cohorts.add(cohort)
        cohort_2 = cohorttest.get_cohort(cohort_name_2,cohort_desc_2,None)
        sample.cohorts.add(cohort_2)
        return sample

    def create_sample_sources(self, sample_number=number,gwas=gwas_id,pmid=pmid,doi=doi):
        return Sample.objects.create(
            sample_number=sample_number,
            source_GWAS_catalog=gwas,
            source_PMID = pmid,
            source_DOI = doi
        )

    def test_sample(self):
        ## Simple Sample object
        sample_1 = self.get_sample(test_sample_number)
        # Instance
        self.assertTrue(isinstance(sample_1, Sample))
        # Variables
        self.assertEqual(sample_1.sample_number, test_sample_number)
        self.assertIsNotNone(sample_1.display_samples)
        # Other methods
        self.assertRegex(sample_1.__str__(), r'^Sample\s\d+')
        self.assertIsNone(sample_1.sample_cases_percent)
        self.assertIsNone(sample_1.display_sampleset)

        ## Sample object with numbers
        sample_2 = self.create_sample_numbers()
        # Instance
        self.assertTrue(isinstance(sample_2, Sample))
        # Variables
        self.assertEqual(sample_2.sample_number, self.number)
        self.assertEqual(sample_2.sample_cases, self.cases)
        self.assertEqual(sample_2.sample_controls, self.controls)
        self.assertEqual(sample_2.sample_percent_male, self.male)
        self.assertEqual(sample_2.sample_cases_percent, round((self.cases/self.number)*100,2))
        # Other methods
        self.assertIsNotNone(sample_2.display_samples)
        self.assertIsNotNone(sample_2.display_samples_for_table)
        self.assertIsNotNone(sample_2.display_sample_number_detail)
        self.assertIsNotNone(sample_2.display_sample_category_number)
        self.assertIsNotNone(sample_2.display_sample_gender_percentage)
        self.assertEqual(sample_2.display_sample_number_total, str(self.number)+' individuals')

        ## Sample object with ancestry
        sample_3 = self.create_sample_ancestry()
        # Instance
        self.assertTrue(isinstance(sample_3, Sample))
        # Variables
        self.assertEqual(sample_3.ancestry_broad, self.a_broad)
        self.assertEqual(sample_3.ancestry_free, self.a_free)
        self.assertEqual(sample_3.ancestry_country, self.a_country)
        self.assertEqual(sample_3.ancestry_additional, self.a_additional)
        # Other methods
        self.assertEqual(sample_3.display_ancestry, self.a_broad)
        self.assertEqual(sample_3.display_ancestry_inline, self.a_broad)
        sample_3.ancestry_free = self.a_free_2
        self.assertEqual(sample_3.display_ancestry, '{}<br/><small>({})</small>'.format(self.a_broad, self.a_free_2))
        self.assertEqual(sample_3.display_ancestry_inline, '{} <small>({})</small>'.format(self.a_broad, self.a_free_2))

        ## Sample with cohorts
        sample_4 = self.create_sample_cohorts()
        # Instance
        self.assertTrue(isinstance(sample_4, Sample))
        # Other methods
        list_cohort_names = [cohort_name, cohort_name_2]
        self.assertEqual(sample_4.list_cohortids(),list_cohort_names)

        ## Sample with sources
        sample_5 = self.create_sample_sources()
        # Instance
        self.assertTrue(isinstance(sample_5, Sample))
        # Variables
        self.assertEqual(sample_5.source_GWAS_catalog, self.gwas_id)
        self.assertEqual(sample_5.source_PMID, self.pmid)
        self.assertEqual(sample_5.source_DOI, self.doi)
        # Other methods
        sources = sample_5.display_sources
        self.assertEqual(sources['GCST'], self.gwas_id)
        self.assertEqual(sources['PMID'], self.pmid)
        self.assertEqual(sources['DOI'], self.doi)


class SampleSetTest(TestCase):
    ''' Test the SampleSet model '''
    sampleset_name="Test_SampleSet"
    sample_set_id = 'PSS000001'
    test_ancestry_2 = ['European','African']
    test_ancestry_3 = ['East Asian','African']

    def create_sampleset(self, num):
        sampletest = SampleTest()
        samples = []
        # Create samples objects
        for i in range(1,test_sample_count+1):
            sample = sampletest.get_sample(300+i)
            samples.append(sample)

        # Create SampleSet object and add list of Samples
        sampleset = SampleSet.objects.create(num=num)
        sampleset.samples.set(samples)
        sampleset.name = self.sampleset_name
        sampleset.set_ids(num)
        return sampleset

    def create_sampleset_ancestry(self, num, ancestry_list):
        sampletest = SampleTest()
        samples = []

        # Create samples objects
        for i in range(1,len(ancestry_list)+1):
            sample = sampletest.create_sample_ancestry(sample_number=i,broad=ancestry_list[i-1])
            self.assertRegex(sample.__str__(), r'\s\-\s'+ancestry_list[i-1])
            samples.append(sample)

        # Create SampleSet object and add list of Samples
        sampleset = SampleSet.objects.create(num=num)
        sampleset.samples.set(samples)
        sampleset.name = self.sampleset_name
        return sampleset

    def test_sampleset_1(self):
        id = default_num
        sampleset = self.create_sampleset(id)
        sampleset.set_ids(id)
        # Instance
        self.assertTrue(isinstance(sampleset, SampleSet))
        # Variables
        self.assertEqual(sampleset.id, self.sample_set_id)
        self.assertTrue(len(sampleset.samples.all()) != 0)
        self.assertTrue(sampleset.name, self.sampleset_name)
        ancestry = '-'
        self.assertEqual(sampleset.samples_ancestry, ancestry)
        self.assertEqual(sampleset.samples_combined_ancestry_key, 'OTH')
        # Other methods
        self.assertEqual(sampleset.__str__(),  self.sample_set_id)
        self.assertEqual(sampleset.count_samples, test_sample_count)
        sample_1 = sampleset.samples.all()[0]
        self.assertRegex(sample_1.__str__(), r'^Sample\s\d+')
        self.assertTrue(isinstance(sample_1.display_sampleset, SampleSet))
        self.assertEqual(sample_1.display_sampleset, sampleset)
        count_ind = 0
        for sample in sampleset.samples.all():
            count_ind += sample.sample_number
        self.assertEqual(sampleset.count_individuals, count_ind)


    def test_sampleset_2(self):
        id = default_num + 1
        sampleset_2 = self.create_sampleset_ancestry(id,self.test_ancestry_2)
        # Instance
        self.assertTrue(isinstance(sampleset_2, SampleSet))
        # Other methods
        ancestry_2 = ', '.join(self.test_ancestry_2)
        self.assertEqual(sampleset_2.samples_ancestry, ancestry_2)
        self.assertEqual(sampleset_2.samples_combined_ancestry_key, 'MAE')
        self.assertEqual(sampleset_2.get_ancestry_key(','.join(self.test_ancestry_2)), 'MAE')
        for desc, key in constants.ANCESTRY_MAPPINGS.items():
            self.assertEqual(sampleset_2.get_ancestry_key(desc), key)


    def test_sampleset_3(self):
        id = default_num + 2
        sampleset_3 = self.create_sampleset_ancestry(id,self.test_ancestry_3)
        ancestry_3 = ', '.join(self.test_ancestry_3)
        self.assertEqual(sampleset_3.samples_ancestry, ancestry_3)
        self.assertEqual(sampleset_3.samples_combined_ancestry_key, 'MAO')
        # Test extra case for 'get_ancestry_key'
        anc_key = sampleset_3.get_ancestry_key(ancestry_3)
        self.assertEqual(anc_key, 'MAO')


class ScoreTest(TestCase):
    ''' Test the Score model '''
    name = 'PGS_name_1'
    score_id = 'PGS000001'
    v_number = 10
    v_build = 'GRCh38'
    m_name = 'SNP'
    m_params = 'method params'
    trait_count = 2
    s_ancestries = {
        "eval": {
            "dist": {
                "AFR": 16.7,
                "AMR": 16.7,
                "EUR": 58.3,
                "MAE": 8.3
            },
            "count": 12
        },
        "dev": {
            "dist": {
                "EUR": 100
            },
            "count": 1
        },
        "gwas": {
            "dist": {
                "EUR": 40.3,
                "MAE": 53.3,
                "SAS": 6.4
            },
            "count": 365042
        }
    }
    weight_type = 'beta'

    def create_score(self, num, name=name, var_number=v_number, build=v_build, m_name=m_name, m_params=m_params, w_type=weight_type):
        pubtest = PublicationTest()
        pub = pubtest.get_publication_doi(num)

        score = Score.objects.create(
            num=num,
            name=name,
            variants_number=var_number,
            variants_genomebuild=build,
            publication_id=pub.num,
            method_name=m_name,
            method_params=m_params,
            weight_type=w_type
        )
        score.set_score_ids(score.num)
        score.save()

        # EFO Trait
        efotraittest = EFOTraitTest()
        trait_1 = efotraittest.get_efo_trait(efo_id, efo_name, efo_desc)
        score.trait_efo.add(trait_1)
        trait_2 = efotraittest.get_efo_trait(efo_id_2, efo_name_2, efo_desc_2)
        score.trait_efo.add(trait_2)

        # Samples
        sampletest = SampleTest()
        # Sample variants
        sample_1 = sampletest.get_sample(test_sample_number)
        score.samples_variants.add(sample_1)
        # Sample training
        sample_2 = sampletest.get_sample(test_sample_number)
        score.samples_training.add(sample_2)

        return score


    def get_score(self, num_id):
        try:
            score = Score.objects.get(num=num_id)
        except Score.DoesNotExist:
            score = self.create_score(num_id)
        return score


    def test_score(self):
        id = default_num
        # Score creation
        score = self.get_score(id)
        # Instance
        self.assertTrue(isinstance(score, Score))
        # Variables
        self.assertEqual(score.id, self.score_id)
        self.assertEqual(score.name, self.name)
        self.assertEqual(score.method_name, self.m_name)
        self.assertEqual(score.method_params, self.m_params)
        self.assertEqual(score.variants_genomebuild, self.v_build)
        self.assertTrue(score.flag_asis)
        self.assertIsNotNone(score.license)
        self.assertTrue(score.has_default_license)
        self.assertEqual(score.weight_type, self.weight_type)

        score.license = "Not the default one"
        self.assertFalse(score.has_default_license)

        # Other methods
        self.assertEqual(score.__str__(),  score.id+" | "+score.name+" | ("+score.publication.__str__()+")")
        self.assertRegex(score.link_filename, r'^PGS\d+\.txt\.gz$')
        self.assertRegex(score.ftp_scoring_file, r'^http.+PGS\d+.*$')
        ftp_hm_files = score.ftp_harmonized_scoring_files
        self.assertEqual(len(ftp_hm_files.keys()), 2)
        genomebuild = constants.GENEBUILDS[0]
        self.assertRegex(ftp_hm_files[genomebuild]['positions'], r'^http.+PGS\d+.*$')

        # Fetch publication object and number of associated score(s)
        pub = Publication.objects.get(num=id)
        self.assertEqual(pub.scores_count, 1)
        self.assertEqual(pub.scores_evaluated_count, 0)
        self.assertEqual(list(pub.scores_evaluated), [])
        self.assertEqual(list(pub.scores_developed), [score.id])
        pgs_associations = pub.associated_pgs_ids
        for a_type in pgs_associations.keys():
            pgs_associations[a_type] = list(pgs_associations[a_type])
        self.assertEqual(pgs_associations, { 'development': [score.id], 'evaluation': [] })

        # Test trait/score association
        efo = score.trait_efo.all()
        self.assertEqual(efo[0].scores_count, 1)
        self.assertEqual(efo[0].associated_pgs_ids, [score.id])
        self.assertEqual(len(score.trait_efo.all()), self.trait_count)
        list_traits = [(efo_id,efo_name),(efo_id_2,efo_name_2)]
        self.assertListEqual(score.list_traits, list_traits)

        # Test sample/score association
        self.assertEqual(len(score.samples_variants.all()), 1)
        sample_v = score.samples_variants.all()[0]
        self.assertRegex(sample_v.__str__(), r'^Sample\s\d+')
        self.assertEqual(len(score.samples_training.all()), 1)
        sample_t = score.samples_training.all()[0]
        self.assertRegex(sample_t.__str__(), r'^Sample\s\d+')
        # Add ancestry data to the Score instance
        score.ancestries = self.s_ancestries
        score.save()
        self.assertEqual(score.ancestries, self.s_ancestries)
        self.assertIsNotNone(score.display_ancestry_html)

        # Test cohort/score association
        cohorttest = CohortTest()
        cohort = cohorttest.get_cohort(cohort_name, cohort_desc, cohort_others)
        sample_t.cohorts.add(cohort)
        self.assertEqual(cohort.associated_pgs_ids, { 'development': [score.id], 'evaluation': [] })

        # Score 2
        score_2 = self.get_score(default_num+1)
        self.assertIsNone(score_2.ancestries)
        self.assertEqual(score_2.display_ancestry_html,'')


class TraitCategoryTest(TestCase):
    ''' Test the Trait Category '''
    trait_label = 'Cancer'
    trait_colour = '#BC80BD'
    trait_parent = 'neoplasm'

    def create_trait_category(self, label=trait_label, colour=trait_colour, parent=trait_parent):
        return TraitCategory.objects.create(label=label,colour=colour,parent=parent)

    def test_trait_category(self):

        trait_category = self.create_trait_category()
        # Instance
        self.assertTrue(isinstance(trait_category, TraitCategory))
        # Variables
        self.assertEqual(trait_category.label, self.trait_label)
        self.assertEqual(trait_category.colour, self.trait_colour)
        self.assertEqual(trait_category.parent, self.trait_parent)
        # Other methods
        self.assertEqual(trait_category.__str__(), self.trait_label)

        # Test to link Trait category to an EFOTrait
        efotraittest = EFOTraitTest()
        trait = efotraittest.get_efo_trait(efo_id, efo_name, efo_desc)
        trait_category.efotraits.add(trait)
        trait.save()
        self.assertEqual(trait.category_labels, trait_category.label)
        self.assertNotEqual(trait.display_category_labels, '')
        category_label =  r'^<div>.*'+trait_category.label+r'.*</div>$'
        self.assertRegex(trait.display_category_labels, category_label)
        self.assertEqual(trait.category_list, [trait_category])
        self.assertEqual(trait.category_labels_list, [trait_category.label])
        self.assertNotEqual(trait.display_category_labels,'')

        # Test to count scores per trait category
        scoretest = ScoreTest()
        score_range = 2
        score_id = default_num
        for i in range(score_range):
            score = scoretest.get_score(score_id)
            score.trait_efo.add(trait)
            score_id += 1
        self.assertEqual(trait_category.count_scores, score_range)


class EFOTrait_OntologyTest(TestCase):
    ''' Test the EFOTrait_Ontology model '''

    def create_efo_trait_ontology(self, efo_id ,label, desc, syn, terms):
        return EFOTrait_Ontology.objects.create(id=efo_id,label=label,description=desc,synonyms=syn,mapped_terms=terms)

    def test_efo_trait_ontology(self):

        scoretest = ScoreTest()
        score_1 = scoretest.get_score(default_num)
        score_2a = scoretest.get_score(default_num+1)
        score_2b = scoretest.get_score(default_num+2)
        associated_pgs_1 = [score_1]
        associated_pgs_2 = [score_2a,score_2b]

        efo_trait_1 = self.create_efo_trait_ontology(efo_id=efo_id,label=efo_name, desc=efo_desc, syn=efo_synonyms, terms=efo_mapped_terms)
        for score in associated_pgs_1:
            efo_trait_1.scores_direct_associations.add(score)

        # Instance
        self.assertTrue(isinstance(efo_trait_1, EFOTrait_Ontology))
        # Variables
        self.assertIsNotNone(efo_trait_1.label)
        self.assertIsNotNone(efo_trait_1.url)
        self.assertIsNotNone(efo_trait_1.description)
        self.assertEqual(efo_trait_1.id, efo_id)
        self.assertEqual(efo_trait_1.label, efo_name)
        self.assertEqual(efo_trait_1.description, efo_desc)
        self.assertEqual(efo_trait_1.synonyms, efo_synonyms)
        self.assertEqual(efo_trait_1.mapped_terms, efo_mapped_terms)
        self.assertEqual(efo_trait_1.synonyms_list, efo_synonyms_list)
        self.assertEqual(efo_trait_1.mapped_terms_list, efo_mapped_terms_list)
        self.assertEqual(len(efo_trait_1.scores_direct_associations.all()), len(associated_pgs_1))
        self.assertEqual(efo_trait_1.scores_direct_associations.all()[0].num, default_num)
        self.assertEqual(efo_trait_1.associated_pgs_ids, [x.id for x in associated_pgs_1])
        # Other methods
        self.assertEqual(efo_trait_1.__str__(), efo_id+' | '+efo_name+' ')
        label_url =  r'^\<a\s.*href=.+\/trait\/'+efo_id+r'.*\>'+efo_name+r'\<\/a\>$'
        self.assertRegex(efo_trait_1.display_label, label_url)
        id_url = r'^\<a\s.*href=.+\>'+efo_id+r'\<\/a\>$'
        self.assertRegex(efo_trait_1.display_ext_url, id_url)


        # Test empty synonyms & mapped_terms
        efo_trait_2 = self.create_efo_trait_ontology(efo_id=efo_id_2,label=efo_name_2, desc=efo_desc_2, syn=None,terms=None)
        for score in associated_pgs_2:
            efo_trait_2.scores_direct_associations.add(score)

        efo_trait_2.parent_traits.add(efo_trait_1)
        # Instance
        self.assertTrue(isinstance(efo_trait_2, EFOTrait_Ontology))
        # Other methods
        self.assertEqual(efo_trait_2.synonyms_list, [])
        self.assertEqual(efo_trait_2.mapped_terms_list, [])
        self.assertEqual(efo_trait_2.parent_traits.all()[0], efo_trait_1)
        self.assertEqual(len(efo_trait_2.scores_direct_associations.all()), len(associated_pgs_2))
        self.assertEqual(efo_trait_2.scores_direct_associations.all()[0].num, default_num+1)
        self.assertEqual(efo_trait_2.associated_pgs_ids, [x.id for x in associated_pgs_2])
        self.assertEqual(efo_trait_2.display_child_traits_list, [])

        efo_trait_1.child_traits.add(efo_trait_2)
        for score in efo_trait_2.scores_direct_associations.all():
            efo_trait_1.scores_child_associations.add(score)
        self.assertEqual(efo_trait_1.child_traits.all()[0], efo_trait_2)
        self.assertEqual(len(efo_trait_1.scores_child_associations.all()), len(associated_pgs_2))
        self.assertEqual(efo_trait_1.scores_child_associations.all()[0].num, default_num+1)
        self.assertEqual(efo_trait_1.child_associated_pgs_ids, [x.id for x in associated_pgs_2])
        display_child = r'^\<a\s.*href=".+'+efo_id_2+'"\s*>'+efo_name_2+r'</a>$'
        self.assertRegex(efo_trait_1.display_child_traits_list[0], display_child)


class EmbargoedPublicationTest(TestCase):
    def create_embargoed_publication(self, publication_id, author_name, publication_title):
        return EmbargoedPublication.objects.create(id=publication_id, firstauthor=author_name, title=publication_title)

    def test_embargoed_publication(self):
        publication_id = 'PGP000007'
        publication_title = 'This is the title'
        e_publication = self.create_embargoed_publication(publication_id=publication_id, author_name=firstauthor, publication_title=publication_title)
        # Instance
        self.assertTrue(isinstance(e_publication, EmbargoedPublication))
        # Variables
        self.assertEqual(e_publication.id, publication_id)
        self.assertEqual(e_publication.firstauthor, firstauthor)
        self.assertEqual(e_publication.title, publication_title)


class EmbargoedScoreTest(TestCase):
    def create_embargoed_score(self, score_id, author_name, reported_trait):
        return EmbargoedScore.objects.create(id=score_id, firstauthor=author_name, trait_reported=reported_trait)

    def test_embargoed_score(self):
        score_id = 'PGS000018'
        trait = 'Coronary artery disease'
        e_score = self.create_embargoed_score(score_id=score_id, author_name=firstauthor, reported_trait=trait)
        # Instance
        self.assertTrue(isinstance(e_score, EmbargoedScore))
        # Variables
        self.assertEqual(e_score.id, score_id)
        self.assertEqual(e_score.firstauthor, firstauthor)
        self.assertEqual(e_score.trait_reported, trait)


class EvaluatedScoreTest(TestCase):
    ''' Test the EvaluatedScore model '''

    def create_evaluatedscore(self, publication, scores):
        # EvaluatedScore
        es = EvaluatedScore.objects.create(publication=publication)
        es.scores_evaluated.set(scores)
        return es

    def test_evaluatedscore(self):
        # Publication
        pubtest = PublicationTest()
        pub = pubtest.get_publication_doi(default_num)

        # Scores
        scoretest = ScoreTest()
        score_1 = scoretest.get_score(default_num)
        score_2 = scoretest.get_score(default_num+1)
        scores = [score_1, score_2]
        score_ids = [x.id for x in scores]

        evaluatedscore = self.create_evaluatedscore(pub,scores)
        # Instance
        self.assertTrue(isinstance(evaluatedscore, EvaluatedScore))
        # Variables
        self.assertEqual(evaluatedscore.publication.num, default_num)
        self.assertEqual(len(evaluatedscore.scores_evaluated.all()), 2)
        self.assertEqual(len(evaluatedscore.evaluated_scores_ids),2)
        self.assertEqual(evaluatedscore.evaluated_scores_ids,score_ids)


class RetiredScoreTest(TestCase):
    ''' Test the Retired model '''
    def create_retired(self, data_id, pub_doi, retirement_notes):
        return Retired.objects.create(id=data_id, doi=pub_doi, notes=retirement_notes)

    def test_retired_score(self):
        score_id = 'PGS000999'
        score_doi = constants.PGS_CITATIONS[0]['doi']
        score_notes = 'This score has been retired'
        retired_score = self.create_retired(score_id, score_doi, score_notes)
        # Instance
        self.assertTrue(isinstance(retired_score, Retired))
        # Variables
        self.assertEqual(retired_score.id, score_id)
        self.assertEqual(retired_score.doi, score_doi)
        self.assertEqual(retired_score.notes, score_notes)
