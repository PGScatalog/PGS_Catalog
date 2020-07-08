from django.test import TestCase
from catalog.models import *
from datetime import datetime

test_sample_number = 5
test_sample_count  = 7

class CohortTest(TestCase):
    """ Test the Cohort model """
    name = "ABC"
    desc = "Cohort description"

    def create_cohort(self, name_short=name,name_full=desc):
        return Cohort.objects.create(name_short=name_short,name_full=name_full)

    def test_cohort(self):
        cohort= self.create_cohort()
        # Instance
        self.assertTrue(isinstance(cohort, Cohort))
        # Variables
        self.assertEqual(cohort.name_short, self.name)
        self.assertEqual(cohort.name_full, self.desc)
        # Other methods
        self.assertEqual(cohort.__str__(), cohort.name_short)
        name_url =  r'^\<a\s.*href=.+\/cohort\/'+cohort.name_short+'_'+str(cohort.id)+r'.*\>'+cohort.name_short+r'\<\/a\>$'
        #self.assertRegexpMatches(cohort.display_cohort_name, name_url)


class DemographicTest(TestCase):
    """ Test the Demographic model """

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

    def test_demographic(self):

        # Type "median" - no variability
        a_type = 'median'
        a_estimate = 10
        a_unit = 'years'
        a_range = '[0.0,20.0]'
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
        regex_range_a = a_range.replace('[','\[').replace(']','\]')
        demo_value_a =  r'^<ul><li>'+a_type.title()+r' : '+str(a_estimate)+r' '+a_unit
        demo_value_a += r'</li><li>'+a_range_type.title()+r' : '+regex_range_a+r' '+a_unit+r'.+$'
        self.assertRegexpMatches(demographic_a.display_value(), demo_value_a)
        values_dict_a = demographic_a.display_values_dict()
        self.assertEqual(values_dict_a[a_type], str(a_estimate))
        self.assertEqual(values_dict_a[a_range_type], a_range)
        self.assertEqual(values_dict_a['unit'], a_unit)

        # Type "mean" - no range
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
        self.assertRegexpMatches(demographic_b.display_value(), demo_value_b)
        values_dict_b = demographic_b.display_values_dict()
        self.assertEqual(values_dict_b[b_variability_type], b_variability)

        # Type "mean" - no variability
        c_type = 'mean'
        c_estimate = 11.1
        c_unit = 'years'
        c_range = '[10.0,12.0]'
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
        regex_range_c = c_range.replace('[','\[').replace(']','\]')
        demo_value_c =  r'^<ul><li>'+c_type.title()+r' : '+str(c_estimate)+r' '+c_unit
        demo_value_c += r'</li><li><span.+>'+c_range_type.title()+r'</span> : '+regex_range_c+r' '+c_unit+r'.+$'
        self.assertRegexpMatches(demographic_c.display_value(), demo_value_c)

        # Type "mean" - no estimate
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
        self.assertRegexpMatches(demographic_d.display_value(), demo_value_d)


class EFOTraitTest(TestCase):
    """ Test the EFOTrait model """
    efo_id   = 'EFO_0000305'
    efo_name = 'breast carcinoma'
    efo_desc = 'A carcinoma that arises from epithelial cells of the breast [MONDO: DesignPattern]'
    efo_synonyms_list = ['CA - Carcinoma of breast','Carcinoma of breast NOS','Mammary Carcinoma, Human']
    efo_synonyms = ' | '.join(efo_synonyms_list)
    efo_mapped_terms_list = ['OMIM:615554','NCIT:C4872','UMLS:C0678222']
    efo_mapped_terms = ' | '.join(efo_mapped_terms_list)

    def create_efo_trait(self, efo_id=efo_id,label=efo_name, desc=efo_desc, syn=efo_synonyms, terms=efo_mapped_terms):
        return EFOTrait.objects.create(id=efo_id,label=label,description=desc,synonyms=syn,mapped_terms=terms)

    def test_efo_trait(self):
        efo_trait_1 = self.create_efo_trait()
        # Instance
        self.assertTrue(isinstance(efo_trait_1, EFOTrait))
        # Variables
        self.assertIsNotNone(efo_trait_1.label)
        self.assertIsNotNone(efo_trait_1.url)
        self.assertIsNotNone(efo_trait_1.description)
        self.assertEqual(efo_trait_1.id, self.efo_id)
        self.assertEqual(efo_trait_1.label, self.efo_name)
        self.assertEqual(efo_trait_1.description, self.efo_desc)
        self.assertEqual(efo_trait_1.synonyms, self.efo_synonyms)
        self.assertEqual(efo_trait_1.mapped_terms, self.efo_mapped_terms)
        self.assertEqual(efo_trait_1.synonyms_list, self.efo_synonyms_list)
        self.assertEqual(efo_trait_1.mapped_terms_list, self.efo_mapped_terms_list)
        # Other methods
        self.assertEqual(efo_trait_1.__str__(), self.efo_id+' | '+self.efo_name+' ')
        label_url =  r'^\<a\s.*href=.+\/trait\/'+self.efo_id+r'.*\>'+self.efo_name+r'\<\/a\>$'
        self.assertRegexpMatches(efo_trait_1.display_label, label_url)
        id_url = r'^\<a\s.*href=.+\>'+self.efo_id+r'</a>.+$'
        self.assertRegexpMatches(efo_trait_1.display_id_url(), id_url)
        efo_trait_1.parse_api()
        self.assertEqual(efo_trait_1.label, self.efo_name)
        self.assertEqual(efo_trait_1.description, self.efo_desc)
        self.assertIsNotNone(efo_trait_1.url)

        # Test empty synonyms & mapped_terms
        efo_trait_2 = self.create_efo_trait(efo_id='EFO_0000306', syn=None, terms=None)
        # Instance
        self.assertTrue(isinstance(efo_trait_2, EFOTrait))
        # Other methods
        self.assertEqual(efo_trait_2.synonyms_list, [])
        self.assertEqual(efo_trait_2.mapped_terms_list, [])


class MetricTest(TestCase):
    """ Test the Metric model """

    def create_performance(self, num):
        performancetest = PerformanceTest()
        performance = performancetest.create_performance(num)
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
        id = 500
        performance = self.create_performance(id)

        # Type "Effect size"
        e_type = 'Effect Size'
        e_name = 'Beta'
        e_name_short = 'β'
        e_estimate = -0.7
        metric_effect = self.create_metric(performance.num,e_type,e_name,e_name_short,e_estimate,'years',0.15,None)
        # Instance
        self.assertTrue(isinstance(metric_effect, Metric))
        # Other methods
        self.assertEqual(metric_effect.display_value(),str(e_estimate))
        self.assertEqual(metric_effect.name_tuple(), (e_name,e_name_short))
        self.assertEqual(metric_effect.__str__(), '{} ({}): {}'.format(e_name,e_name_short,e_estimate))

        # Type "Classification Metric"
        c_type = 'Classification Metric'
        c_name = 'Concordance Statistic'
        c_name_short = 'C-index'
        c_estimate = 0.655
        c_ci = '[0.605,0.667]'
        metric_class = self.create_metric(performance.num,c_type,c_name,c_name_short,c_estimate,'',None,c_ci)
        # Instance
        self.assertTrue(isinstance(metric_class, Metric))
        # Other methods
        self.assertEqual(metric_class.display_value(), str(c_estimate)+' '+c_ci)
        self.assertEqual(metric_class.name_tuple(), (c_name,c_name_short))
        self.assertEqual(metric_class.__str__(), '{} ({}): {} {}'.format(c_name,c_name_short,c_estimate,c_ci))


        # Type "Other Metric"
        o_type = 'Other Metric'
        o_name = 'correlation (r)'
        o_name_short = None
        o_estimate = 0.29
        o_ci = '[0.231,0.349]'
        metric_other = self.create_metric(performance.num,o_type,o_name,o_name_short,o_estimate,'',None,o_ci)
        # Instance
        self.assertTrue(isinstance(metric_other, Metric))
        # Other methods
        self.assertEqual(metric_other.display_value(), str(o_estimate)+' '+o_ci)
        self.assertEqual(metric_other.name_tuple(), (o_name,o_name))
        self.assertEqual(metric_other.__str__(), '{}: {} {}'.format(o_name,o_estimate,o_ci))


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
        self.assertEqual(perf_dict['effect_sizes'], [{ 'labels': (e_name,e_name_short), 'value': str(e_estimate) }])
        c_value = metric_class.display_value().replace(',', ', ')
        self.assertEqual(perf_dict['class_acc'], [{ 'labels': (c_name,c_name_short), 'value': c_value }])
        o_value = metric_other.display_value().replace(',', ', ')
        self.assertEqual(perf_dict['othermetrics'], [{ 'labels': (o_name,o_name), 'value': o_value }])

class PerformanceTest(TestCase):
    """ Test the Performance model """
    perf_id = 'PPM000001'
    phenotype_reported = 'New reported phenotype'

    def create_performance(self, num):
        # Score
        extra_num = num
        scoretest = ScoreTest()
        score = scoretest.create_score(num=extra_num)

        # Publication
        extra_num += 1
        pubtest = PublicationTest()
        pub = pubtest.create_publication_by_doi(num=extra_num)

        # Sample Set
        extra_num += 1
        samplesettest = SampleSetTest()
        sampleset = samplesettest.create_sampleset(num=extra_num)

        performance = Performance.objects.create(num=num, score=score, publication=pub, sampleset=sampleset)

        # EFO trait
        extra_num += 1
        efotraittest = EFOTraitTest()
        efotrait = efotraittest.create_efo_trait('EFO_0000'+str(extra_num),'efotrait','This is an EFO trait')
        performance.phenotyping_efo.add(efotrait)

        performance.phenotyping_reported = self.phenotype_reported

        return performance

    def test_performance(self):
        id = 1

        performance = self.create_performance(id)
        performance.set_performance_id(id)
        # Instance
        self.assertTrue(isinstance(performance, Performance))
        # Variables
        self.assertEqual(performance.id, self.perf_id)
        self.assertEqual(len(performance.samples()), test_sample_count)
        # Other methods
        self.assertRegexpMatches(performance.__str__(), r'^'+self.perf_id+r' \| PGS\d+ -> PSS\d+$')
        pub_ext = performance.publication_withexternality.split('|')
        self.assertEqual(pub_ext[-2], 'E')
        self.assertNotEqual(pub_ext[-1], '') # Is preprint
        sampleset = performance.sampleset
        self.assertEqual(sampleset.count_performances, 1)
        self.assertEqual(performance.display_trait['efo'][0], performance.phenotyping_efo.all()[0])
        self.assertEqual(performance.display_trait['reported'], self.phenotype_reported)
        self.assertTrue(isinstance(performance.publication, Publication))
        self.assertEqual(performance.publication.scores_evaluated, 1)
        self.assertEqual(performance.associated_pgs_id, performance.score.id)
        cohort = CohortTest.create_cohort('HIJ', 'Example of cohort')
        sampleset.samples.all()[0].cohorts.add(cohort)
        self.assertEqual(cohort.associated_pgs_ids, { 'development': [], 'evaluation': [performance.score.id] })

        id = 2000
        performance_2 = self.create_performance(id)
        performance_2.set_performance_id(id)
        # Instance
        self.assertTrue(isinstance(performance_2, Performance))
        # Other methods
        pubtest = PublicationTest()
        pub = pubtest.create_publication_by_pmid(num=id+10)
        performance_2.publication = pub
        performance_2.score.publication = pub
        pub_ext_2 = performance_2.publication_withexternality.split('|')
        self.assertEqual(pub_ext_2[-2], 'D')
        self.assertEqual(pub_ext_2[-1], '') # Is not preprint


class PublicationTest(TestCase):
    """ Test the Publication model """
    first_author = "Smith J"

    def create_publication_by_doi(self, num, date="2018-10-01", id="10.1016/j.jacc.2018.07.079",author=first_author,journal='bioRxiv'):
        date_list = date.split('-')
        date_formated = datetime(int(date_list[0]),int(date_list[1]),int(date_list[2]))
        pub = Publication.objects.create(num=num, date_publication=date_formated, doi=id, firstauthor=author, journal=journal)
        pub.set_publication_ids(num)
        return pub

    def create_publication_by_pmid(self, num, date="2015-04-08", id=25855707, journal="Lancet"):
        date_list = date.split('-')
        date_formated = datetime(int(date_list[0]),int(date_list[1]),int(date_list[2]))
        pub = Publication.objects.create(num=num, date_publication=date_formated, PMID=id, journal=journal)
        pub.set_publication_ids(num)
        return pub

    def test_publication(self):
        id = 1
        pub_doi = self.create_publication_by_doi(id)
        pub_doi.set_publication_ids(id)
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

        id = 2
        pub_pmid = self.create_publication_by_pmid(id)
        pub_pmid.set_publication_ids(id)
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
    """ Test the Release model """

    date_list = ['2020','03','20']
    date_string = '-'.join(date_list)
    date_formated = datetime(int(date_list[0]),int(date_list[1]),int(date_list[2]))
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
        extra_num = 100
        scoretest = ScoreTest()
        score1 = scoretest.create_score(num=extra_num)
        score1.date_released = self.date_formated
        score1.save()
        ids_list['score'].append(score1.id)
        # - Score 2
        extra_num += 5
        score2 = scoretest.create_score(num=extra_num)
        score2.date_released = self.date_formated
        score2.save()
        ids_list['score'].append(score2.id)

        # Performance
        extra_num += 5
        perftest = PerformanceTest()
        perf = perftest.create_performance(num=extra_num)
        perf.date_released = self.date_formated
        perf.save()
        ids_list['perf'].append(perf.id)

        # Publication
        extra_num += 5
        pubtest = PublicationTest()
        pub = pubtest.create_publication_by_doi(num=extra_num)
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
        self.assertEqual(release.__str__(), self.date_string+' 00:00:00')


class SampleTest(TestCase):
    """ Test the Sample model """
    number = 10
    cases = 6
    controls = 4
    male = 40
    a_broad = 'European'
    a_free = 'NR'
    a_free_2 = 'Cambridgeshire'
    a_country = 'France, Germany, Netherlands, Estonia, Finland, Sweden, U.K., NR, U.S.'
    a_additional = 'White European'
    cohort_range = 2
    gwas_id = 'GCST001937'
    pmid = '23535729'

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
        for i in range(1, self.cohort_range+1):
            c_name = 'CS'+str(i)
            cohort = cohorttest.create_cohort(c_name)
            sample.cohorts.add(cohort)
        return sample

    def create_sample_sources(self, sample_number=number,gwas=gwas_id,pmid=pmid):
        return Sample.objects.create(
            sample_number=sample_number,
            source_GWAS_catalog=gwas,
            source_PMID = pmid
        )

    def test_sample(self):
        ## Simple Sample object
        sample_1 = self.create_sample(test_sample_number)
        # Instance
        self.assertTrue(isinstance(sample_1, Sample))
        # Variables
        self.assertEqual(sample_1.sample_number, test_sample_number)
        # Other methods
        self.assertRegexpMatches(sample_1.__str__(), r'^Sample:\s\d+$')
        self.assertIsNotNone(sample_1.display_samples_for_table)

        ## Sample object with numbers
        sample_2 = self.create_sample_numbers()
        # Instance
        self.assertTrue(isinstance(sample_2, Sample))
        # Variables
        self.assertEqual(sample_2.sample_number, self.number)
        self.assertEqual(sample_2.sample_cases, self.cases)
        self.assertEqual(sample_2.sample_controls, self.controls)
        self.assertEqual(sample_2.sample_percent_male, self.male)
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
        sample_3.ancestry_free = 'Cambridgeshire'
        self.assertEqual(sample_3.display_ancestry, '{}<br/>({})'.format(self.a_broad, self.a_free_2))
        self.assertEqual(sample_3.display_ancestry_inline, '{} ({})'.format(self.a_broad, self.a_free_2))

        ## Sample with cohorts
        sample_4 = self.create_sample_cohorts()
        # Instance
        self.assertTrue(isinstance(sample_4, Sample))
        # Other methods
        list_cohort_names = []
        for i in range(1, self.cohort_range+1):
            c_name = 'CS'+str(i)
            list_cohort_names.append(c_name)
        self.assertEqual(sample_4.list_cohortids(),list_cohort_names)

        ## Sample with sources
        sample_5 = self.create_sample_sources()
        # Instance
        self.assertTrue(isinstance(sample_5, Sample))
        # Other methods
        sources = sample_5.display_sources
        self.assertEqual(sources['GCST'], self.gwas_id)
        self.assertEqual(sources['PMID'], self.pmid)


class SampleSetTest(TestCase):
    """ Test the SampleSet model """
    sample_set_id = 'PSS000001'
    test_ancestry = ['European','African']

    def create_sampleset(self, num):

        sampletest = SampleTest()
        samples = []
        # Create samples objects
        for i in range(1,test_sample_count+1):
            sample = sampletest.create_sample(i)
            samples.append(sample)
        # Create SampleSet object and add list of Samples
        sampleset = SampleSet.objects.create(num=num)
        sampleset.samples.set(samples)
        sampleset.set_ids(num)
        return sampleset

    def create_sampleset_ancestry(self, num):

        sampletest = SampleTest()
        samples = []
        # Create samples objects
        for i in range(1,len(self.test_ancestry)+1):
            sample = sampletest.create_sample_ancestry(sample_number=i,broad=self.test_ancestry[i-1])
            samples.append(sample)
        # Create SampleSet object and add list of Samples
        sampleset = SampleSet.objects.create(num=num)
        sampleset.samples.set(samples)
        return sampleset

    def test_sampleset(self):
        id = 1
        sampleset = self.create_sampleset(id)
        sampleset.set_ids(id)
        # Instance
        self.assertTrue(isinstance(sampleset, SampleSet))
        # Variables
        self.assertEqual(sampleset.id, self.sample_set_id)
        self.assertTrue(len(sampleset.samples.all()) != 0)
        self.assertEqual(sampleset.samples_ancestry, '-')
        # Other methods
        self.assertEqual(sampleset.__str__(),  self.sample_set_id)
        self.assertEqual(sampleset.count_samples, test_sample_count)
        sample = sampleset.samples.all()[0]
        self.assertRegexpMatches(sample.__str__(), r'^Sample:\s\d+ | '+sampleset.id+r'$')
        self.assertTrue(isinstance(sample.display_sampleset, SampleSet))
        self.assertEqual(sample.display_sampleset, sampleset)

        id += 1
        sampleset_2 = sampleset = self.create_sampleset_ancestry(id)
        # Instance
        self.assertTrue(isinstance(sampleset_2, SampleSet))
        # Other methods
        ancestry = ', '.join(self.test_ancestry)
        self.assertEqual(sampleset_2.samples_ancestry, ancestry)


class ScoreTest(TestCase):
    """ Test the Score model """
    name = 'PGS_name_1'
    score_id = 'PGS000001'
    v_number = 10
    v_build = 'GRCh38'
    m_name = 'SNP'
    m_params = 'method params'
    trait_range = 2
    trait_prefix = 'EFO_000'
    trait_label_prefix = 'trait '

    def create_score(self, num, name=name, var_number=v_number, build=v_build, m_name=m_name, m_params=m_params):
        pubtest = PublicationTest()
        pub = pubtest.create_publication_by_doi(num=num)

        score = Score.objects.create(
            num=num,
            name=name,
            variants_number=var_number,
            variants_genomebuild=build,
            publication_id=pub.num,
            method_name=m_name,
            method_params=m_params
        )
        score.set_score_ids(score.num)
        score.save()

        # EFO Trait
        efotraittest = EFOTraitTest()
        for i in range(1, self.trait_range+1):
            e_id = self.trait_prefix+str(i)+str(num)
            trait = efotraittest.create_efo_trait(efo_id=e_id,label=self.trait_label_prefix+str(i))
            score.trait_efo.add(trait)

        # Samples
        sampletest = SampleTest()
        # Sample variants
        sample_1 = sampletest.create_sample()
        score.samples_variants.add(sample_1)
        # Sample training
        sample_2 = sampletest.create_sample()
        score.samples_training.add(sample_2)

        return score

    def test_score(self):
        id = 1
        # Score creation
        score = self.create_score(id)
        score.set_score_ids(id)
        # Instance
        self.assertTrue(isinstance(score, Score))
        # Variables
        self.assertEqual(score.id, self.score_id)
        self.assertEqual(score.name, self.name)
        self.assertEqual(score.method_name, self.m_name)
        self.assertEqual(score.method_params, self.m_params)
        self.assertEqual(score.variants_genomebuild, self.v_build)
        self.assertTrue(score.flag_asis)
        # Other methods
        self.assertEqual(score.__str__(),  score.id+" | "+score.name+" | ("+score.publication.__str__()+")")
        self.assertRegexpMatches(score.link_filename, r'^PGS\d+\.txt\.gz$')
        self.assertRegexpMatches(score.ftp_scoring_file, r'^http.+PGS\d+.*$')

        # Fetch publication object and number of associated score(s)
        pub = Publication.objects.get(num=id)
        self.assertEqual(pub.scores_count, 1)
        self.assertEqual(pub.associated_pgs_ids, [score.id])

        # Test trait/score association
        efo = score.trait_efo.all()
        self.assertEqual(efo[0].scores_count, 1)
        self.assertEqual(efo[0].associated_pgs_ids, [score.id])
        self.assertEqual(len(score.trait_efo.all()), self.trait_range)
        list_traits = []
        for i in range(1, self.trait_range+1):
            e_id = self.trait_prefix+str(i)+str(id)
            e_label = self.trait_label_prefix+str(i)
            list_traits.append((e_id,e_label))
        self.assertListEqual(score.list_traits, list_traits)

        # Test sample/score association
        self.assertEqual(len(score.samples_variants.all()), 1)
        sample_v = score.samples_variants.all()[0]
        self.assertRegexpMatches(sample_v.__str__(), r'^Sample:\s\d+ | '+score.id+r'$')
        self.assertEqual(len(score.samples_training.all()), 1)
        sample_t = score.samples_training.all()[0]
        self.assertRegexpMatches(sample_t.__str__(), r'^Sample:\s\d+ | '+score.id+r'$')

        # Test cohort/score association
        cohort = CohortTest.create_cohort('DEF', 'Example of cohort')
        sample_t.cohorts.add(cohort)
        self.assertEqual(cohort.associated_pgs_ids, { 'development': [score.id], 'evaluation': [] })


class TraitCategoryTest(TestCase):
    """ Test the Trait Category """
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
        trait = efotraittest.create_efo_trait('EFO_0000292','bladder carcinoma','A carcinoma that arises from epithelial cells of the urinary bladder')
        trait_category.efotraits.add(trait)
        self.assertEqual(trait.category_labels, trait_category.label)
        self.assertNotEqual(trait.display_category_labels, '')
        category_label =  r'^<div>.*'+trait_category.label+r'.*</div>$'
        self.assertRegexpMatches(trait.display_category_labels, category_label)
        self.assertEqual(list(trait.category_list), [trait_category])

        # Test to count scores per trait category
        scoretest = ScoreTest()
        score_range = 2
        score_id = 200
        for i in range(score_range):
            score = scoretest.create_score(num=score_id)
            score.trait_efo.add(trait)
            score_id += 1
        self.assertEqual(trait_category.count_scores, score_range)


class EFOTrait_OntologyTest(TestCase):
    """ Test the EFOTrait_Ontology model """

    efo_id_1   = 'EFO_0000305'
    efo_name_1 = 'breast carcinoma'
    efo_desc_1 = 'A carcinoma that arises from epithelial cells of the breast [MONDO: DesignPattern]'
    efo_synonyms_list_1 = ['CA - Carcinoma of breast','Carcinoma of breast NOS','Mammary Carcinoma, Human']
    efo_synonyms_1 = ' | '.join(efo_synonyms_list_1)
    efo_mapped_terms_list_1 = ['OMIM:615554','NCIT:C4872','UMLS:C0678222']
    efo_mapped_terms_1 = ' | '.join(efo_mapped_terms_list_1)

    efo_id_2   = 'EFO_1000649'
    efo_name_2 = 'estrogen-receptor positive breast cancer'
    efo_desc_2 = 'a subtype of breast cancer that is estrogen-receptor positive [EFO: 1000649]'

    def create_efo_trait_ontology(self, efo_id ,label, desc, syn, terms):
        return EFOTrait_Ontology.objects.create(id=efo_id,label=label,description=desc,synonyms=syn,mapped_terms=terms)

    def test_efo_trait_ontology(self):

        scoretest = ScoreTest()
        score_num = 825
        score_1 = scoretest.create_score(num=score_num,name="Score_1_for_EFOTrait_OntologyTest", var_number=1)
        score_1.set_score_ids(score_num)
        score_2a = scoretest.create_score(num=score_num+1,name="Score_2a_for_EFOTrait_OntologyTest", var_number=1)
        score_2a.set_score_ids(score_num+1)
        score_2b = scoretest.create_score(num=score_num+2,name="Score_2b_for_EFOTrait_OntologyTest", var_number=1)
        score_2b.set_score_ids(score_num+2)
        associated_pgs_1 = [score_1]
        associated_pgs_2 = [score_2a,score_2b]

        efo_trait_1 = self.create_efo_trait_ontology(
            efo_id=self.efo_id_1,label=self.efo_name_1, desc=self.efo_desc_1, syn=self.efo_synonyms_1,
            terms=self.efo_mapped_terms_1)
        for score in associated_pgs_1:
            efo_trait_1.scores_direct_associations.add(score)

        # Instance
        self.assertTrue(isinstance(efo_trait_1, EFOTrait_Ontology))
        # Variables
        self.assertIsNotNone(efo_trait_1.label)
        self.assertIsNotNone(efo_trait_1.url)
        self.assertIsNotNone(efo_trait_1.description)
        self.assertEqual(efo_trait_1.id, self.efo_id_1)
        self.assertEqual(efo_trait_1.label, self.efo_name_1)
        self.assertEqual(efo_trait_1.description, self.efo_desc_1)
        self.assertEqual(efo_trait_1.synonyms, self.efo_synonyms_1)
        self.assertEqual(efo_trait_1.mapped_terms, self.efo_mapped_terms_1)
        self.assertEqual(efo_trait_1.synonyms_list, self.efo_synonyms_list_1)
        self.assertEqual(efo_trait_1.mapped_terms_list, self.efo_mapped_terms_list_1)
        self.assertEqual(len(efo_trait_1.scores_direct_associations.all()), len(associated_pgs_1))
        self.assertEqual(efo_trait_1.scores_direct_associations.all()[0].num, score_num)
        self.assertEqual(efo_trait_1.associated_pgs_ids, [x.id for x in associated_pgs_1])
        # Other methods
        self.assertEqual(efo_trait_1.__str__(), self.efo_id_1+' | '+self.efo_name_1+' ')
        label_url =  r'^\<a\s.*href=.+\/trait\/'+self.efo_id_1+r'.*\>'+self.efo_name_1+r'\<\/a\>$'
        self.assertRegexpMatches(efo_trait_1.display_label, label_url)
        id_url = r'^\<a\s.*href=.+\>'+self.efo_id_1+r'</a>.+$'
        self.assertRegexpMatches(efo_trait_1.display_id_url(), id_url)


        # Test empty synonyms & mapped_terms
        efo_trait_2 = self.create_efo_trait_ontology(efo_id=self.efo_id_2,label=self.efo_name_2, desc=self.efo_desc_2, syn=None,terms=None)
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
        self.assertEqual(efo_trait_2.scores_direct_associations.all()[0].num, score_num+1)
        self.assertEqual(efo_trait_2.associated_pgs_ids, [x.id for x in associated_pgs_2])
        self.assertEqual(efo_trait_2.display_child_traits_list, [])

        efo_trait_1.child_traits.add(efo_trait_2)
        for score in efo_trait_2.scores_direct_associations.all():
            efo_trait_1.scores_child_associations.add(score)
        self.assertEqual(efo_trait_1.child_traits.all()[0], efo_trait_2)
        self.assertEqual(len(efo_trait_1.scores_child_associations.all()), len(associated_pgs_2))
        self.assertEqual(efo_trait_1.scores_child_associations.all()[0].num, score_num+1)
        self.assertEqual(efo_trait_1.child_associated_pgs_ids, [x.id for x in associated_pgs_2])
        display_child = r'^\<a\s.*href=".+'+self.efo_id_2+'"\s*>'+self.efo_name_2+r'</a>$'
        self.assertRegexpMatches(efo_trait_1.display_child_traits_list[0], display_child)
