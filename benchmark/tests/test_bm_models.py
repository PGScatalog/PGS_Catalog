from django.test import TestCase
from benchmark.models import *

benchmark_db = 'benchmark'
databases_list = ['default',benchmark_db]

test_sample_number = 4 #5

cohort_name = "ABC"
cohort_desc = "Cohort description"

efo_id = 'EFO_0000305'
efo_name = 'breast carcinoma'
efo_desc = 'A carcinoma that arises from epithelial cells of the breast [MONDO: DesignPattern]'

icd_id = "ICD10: C18.0"
icd_label = 'Malignant neoplasm of cecum'
icd_type = "ICD10"

score_id = 'PGS000001'

broad_ancestry = 'European'


class BM_CodingTest(TestCase):
    """ Test the BM_Coding model """
    # Pointer to the database to use
    databases = databases_list

    id = "ICD10: C18.0"
    label = 'Malignant neoplasm of cecum'
    type = "ICD10"

    def create_bm_coding(self, id=icd_id, label=icd_label, type=icd_type):
        return BM_Coding.objects.using(benchmark_db).create(id=id, label=label, type=type)

    def get_bm_coding(self, id, label, type):
        try:
            bm_coding = BM_Coding.objects.using(benchmark_db).get(id=id)
        except BM_Coding.DoesNotExist:
            bm_coding = self.create_bm_coding(id=id, label=label, type=type)
        return bm_coding

    def test_bm_coding(self):
        bm_coding = self.get_bm_coding(icd_id, icd_label, icd_type)
        # Instance
        self.assertTrue(isinstance(bm_coding, BM_Coding))
        # Variables
        self.assertEqual(bm_coding.id, self.id)
        self.assertEqual(bm_coding.label, self.label)
        self.assertEqual(bm_coding.type, self.type)


class BM_CohortTest(TestCase):
    """ Test the BM_Cohort model """
    # Pointer to the database to use
    databases = databases_list

    #name = "ABC"
    #desc = "Cohort description"

    def create_bm_cohort(self, name_short=cohort_name, name_full=cohort_desc):
        return BM_Cohort.objects.using(benchmark_db).create(name_short=name_short,name_full=name_full)

    def get_bm_cohort(self,name_short):
        try:
            bm_cohort = BM_Cohort.objects.using(benchmark_db).get(name_short=name_short)
        except BM_Cohort.DoesNotExist:
            bm_cohort = self.create_bm_cohort(name_short=name_short)
        return bm_cohort

    def test_bm_cohort(self):
        bm_cohort= self.create_bm_cohort()
        # Instance
        self.assertTrue(isinstance(bm_cohort, BM_Cohort))
        # Variables
        self.assertEqual(bm_cohort.__str__(), cohort_name)
        self.assertEqual(bm_cohort.name_short, cohort_name)
        self.assertEqual(bm_cohort.name_full, cohort_desc)


class BM_DemographicTest(TestCase):
    """ Test the BM_Demographic model """
    # Pointer to the database to use
    databases = databases_list

    def create_bm_demographic(self, estimate, estimate_type, unit, range, range_type, variability, variability_type):
        return BM_Demographic.objects.using(benchmark_db).create(
            estimate=estimate,
            estimate_type=estimate_type,
            unit=unit,
            range=range,
            range_type=range_type,
            variability=variability,
            variability_type=variability_type
        )

    def test_bm_demographic(self):

        # Type "median" - no variability
        a_type = 'median'
        a_estimate = 10
        a_unit = 'years'
        a_range = '[0.0,20.0]'
        a_range_type = 'range'
        a_variability = None
        a_variability_type = 'se'
        bm_demographic_a = self.create_bm_demographic(a_estimate,a_type,a_unit,a_range,a_range_type,a_variability,a_variability_type)
        # Instance
        self.assertTrue(isinstance(bm_demographic_a, BM_Demographic))
        # Variables
        self.assertEqual(bm_demographic_a.estimate,a_estimate)
        self.assertEqual(bm_demographic_a.estimate_type,a_type)
        self.assertEqual(bm_demographic_a.unit,a_unit)
        self.assertEqual(bm_demographic_a.range,a_range)
        self.assertEqual(bm_demographic_a.range_type,a_range_type)
        self.assertEqual(bm_demographic_a.variability,a_variability)
        self.assertEqual(bm_demographic_a.variability_type,a_variability_type)
        # Other methods
        self.assertEqual(bm_demographic_a.format_estimate(), a_type+':'+str(a_estimate))
        self.assertIsNone(bm_demographic_a.format_range())
        self.assertIsNone(bm_demographic_a.format_variability())
        self.assertEqual(bm_demographic_a.format_unit(),'unit:'+a_unit)
        self.assertEqual(bm_demographic_a.variability_type_desc(), 'Standard Error')
        regex_range_a = a_range.replace('[','\[').replace(']','\]')
        demo_value_a =  r'^<ul><li>'+a_type.title()+r' : '+str(a_estimate)+r' '+a_unit
        demo_value_a += r'</li><li>'+a_range_type.title()+r' : '+regex_range_a+r' '+a_unit+r'.+$'
        self.assertRegex(bm_demographic_a.display_value(), demo_value_a)
        values_dict_a = bm_demographic_a.display_values_dict()
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
        bm_demographic_b = self.create_bm_demographic(b_estimate,b_type,b_unit,b_range,b_range_type,b_variability,b_variability_type)
        # Instance
        self.assertTrue(isinstance(bm_demographic_b, BM_Demographic))
        # Other methods
        self.assertIsNone(bm_demographic_b.format_range())
        self.assertEqual(bm_demographic_b.format_variability(), '{}:{}'.format(b_variability_type,b_variability))
        demo_value_b =  r'^<ul><li>'+b_type.title()+r' : '+str(b_estimate)+r' '+b_unit
        demo_value_b += r'</li><li><span.+>'+b_variability_type.title()+r'</span> : '+str(b_variability)+r' '+b_unit+r'.+$'
        self.assertRegex(bm_demographic_b.display_value(), demo_value_b)
        values_dict_b = bm_demographic_b.display_values_dict()
        self.assertEqual(values_dict_b[b_variability_type], b_variability)

        # Type "mean" - no variability
        c_type = 'mean'
        c_estimate = 11.1
        c_unit = 'years'
        c_range = '[10.0,12.0]'
        c_range_type = 'iqr'
        c_variability = None
        c_variability_type = 'se'
        bm_demographic_c = self.create_bm_demographic(c_estimate,c_type,c_unit,c_range,c_range_type,c_variability,c_variability_type)
        # Instance
        self.assertTrue(isinstance(bm_demographic_c, BM_Demographic))
        # Variables
        self.assertEqual(bm_demographic_c.estimate_type,c_type)
        # Other methods
        self.assertEqual(bm_demographic_c.range_type_desc(), 'Interquartile range')
        regex_range_c = c_range.replace('[','\[').replace(']','\]')
        demo_value_c =  r'^<ul><li>'+c_type.title()+r' : '+str(c_estimate)+r' '+c_unit
        demo_value_c += r'</li><li><span.+>'+c_range_type.title()+r'</span> : '+regex_range_c+r' '+c_unit+r'.+$'
        self.assertRegex(bm_demographic_c.display_value(), demo_value_c)

        # Type "mean" - no estimate
        d_type = 'mean'
        d_estimate = None
        d_unit = 'years'
        d_range = '[50.0,69.0]'
        d_range_type = 'range'
        d_variability = None
        d_variability_type = 'se'
        demographic_d = self.create_bm_demographic(d_estimate,d_type,d_unit,d_range,d_range_type,d_variability,d_variability_type)
        # Instance
        self.assertTrue(isinstance(demographic_d, BM_Demographic))
        # Other methods
        self.assertIsNone(demographic_d.format_estimate())
        self.assertEqual(demographic_d.format_range(),d_range_type+':'+d_range)
        regex_range_d = d_range.replace('[','\[').replace(']','\]')
        demo_value_d =  r'^'+d_range_type.title()+r' : '+regex_range_d+r' '+d_unit+r'$'
        self.assertRegex(demographic_d.display_value(), demo_value_d)


class BM_EFOTraitTest(TestCase):
    """ Test the BM_EFOTrait model """
    # Pointer to the database to use
    databases = databases_list

    #efo_id = 'EFO_0000305'
    #efo_name = 'breast carcinoma'
    #efo_desc = 'A carcinoma that arises from epithelial cells of the breast [MONDO: DesignPattern]'
    ##efo_synonyms_list = ['CA - Carcinoma of breast','Carcinoma of breast NOS','Mammary Carcinoma, Human']
    ##efo_synonyms = ' | '.join(efo_synonyms_list)
    ##efo_mapped_terms_list = ['OMIM:615554','NCIT:C4872','UMLS:C0678222']
    ##efo_mapped_terms = ' | '.join(efo_mapped_terms_list)

    def create_bm_efo_trait(self, efo_id=efo_id,label=efo_name, desc=efo_desc):#, syn=efo_synonyms, terms=efo_mapped_terms):
        return BM_EFOTrait.objects.using(benchmark_db).create(id=efo_id,label=label,description=desc)#,synonyms=syn,mapped_terms=terms)

    def get_bm_efo_trait(self, bm_efo_id, bm_label, bm_desc):
        try:
            bm_efo_trait = BM_EFOTrait.objects.using(benchmark_db).get(id=bm_efo_id)
        except BM_EFOTrait.DoesNotExist:
            bm_efo_trait = self.create_bm_efo_trait(efo_id=bm_efo_id,label=bm_efo_id, desc=bm_desc)
        return bm_efo_trait

    def test_bm_efo_trait(self):
        bm_efo_trait_1 = self.create_bm_efo_trait()
        # Instance
        self.assertTrue(isinstance(bm_efo_trait_1, BM_EFOTrait))
        # Variables
        self.assertIsNotNone(bm_efo_trait_1.label)
        #self.assertIsNotNone(bm_efo_trait_1.url)
        self.assertIsNotNone(bm_efo_trait_1.description)
        self.assertEqual(bm_efo_trait_1.id, efo_id)
        self.assertEqual(bm_efo_trait_1.label, efo_name)
        self.assertEqual(bm_efo_trait_1.description, efo_desc)
        #self.assertEqual(bm_efo_trait_1.synonyms, self.efo_synonyms)
        #self.assertEqual(bm_efo_trait_1.mapped_terms, self.efo_mapped_terms)
        #self.assertEqual(bm_efo_trait_1.synonyms_list, self.efo_synonyms_list)
        #self.assertEqual(bm_efo_trait_1.mapped_terms_list, self.efo_mapped_terms_list)
        # Other methods
        self.assertEqual(bm_efo_trait_1.__str__(), efo_id+' | '+efo_name+' ')
        label_url =  r'^\<a\s.*href=.+\/benchmark\/'+efo_id+r'.*\>'+efo_name+r'\<\/a\>$'
        self.assertRegex(bm_efo_trait_1.display_label, label_url)
        #label_url =  r'^\<a\s.*href=.+\/trait\/'+self.efo_id+r'.*\>'+self.efo_name+r'\<\/a\>$'
        #self.assertRegex(bm_efo_trait_1.display_label, label_url)
        #id_url = r'^\<a\s.*href=.+\>'+self.efo_id+r'</a>.+$'
        #self.assertRegex(bm_efo_trait_1.display_id_url(), id_url)
        self.assertEqual(bm_efo_trait_1.label, efo_name)
        self.assertEqual(bm_efo_trait_1.description, efo_desc)
        #self.assertIsNotNone(bm_efo_trait_1.url)

        # Coding object(s)
        codingtest = BM_CodingTest()
        bm_coding = codingtest.get_bm_coding(icd_id, icd_label, icd_type)
        bm_efo_trait_1.phenotype_structured.add(bm_coding)
        icd_data = bm_efo_trait_1.display_phenotype_structured
        self.assertTrue(isinstance(bm_efo_trait_1.phenotype_structured.all()[0], BM_Coding))
        coding_display = r'^\<b\>'+icd_id+'\<\/b\>\:\s'+icd_label+'$'
        self.assertRegex(bm_efo_trait_1.display_phenotype_structured[0], coding_display)


        # Test empty synonyms & mapped_terms
        bm_efo_trait_2 = self.create_bm_efo_trait(efo_id='EFO_0000306')#, syn=None, terms=None)
        # Instance
        self.assertTrue(isinstance(bm_efo_trait_2, BM_EFOTrait))


class BM_MetricTest(TestCase):
    """ Test the BM_Metric model """
    # Pointer to the database to use
    databases = databases_list

    def get_bm_performance(self):

        # BM_Cohort object
        cohorttest = BM_CohortTest()
        bm_cohort = cohorttest.get_bm_cohort(cohort_name)

        # BM_Sample object
        sampletest = BM_SampleTest()
        bm_sample = sampletest.get_bm_sample(test_sample_number,bm_cohort)

        # BM_EFOTrait object
        efotraittest = BM_EFOTraitTest()
        bm_efotrait = efotraittest.get_bm_efo_trait(efo_id,efo_name,efo_desc)

        performance_test = BM_PerformanceTest()
        return performance_test.get_bm_performance(bm_sample, bm_efotrait, bm_cohort)

    def create_bm_metric(self, performance_id, type, name, name_short, estimate, unit, se, ci):

        return BM_Metric.objects.using(benchmark_db).create(
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
        bm_performance = self.get_bm_performance()

        # Type "Effect size"
        e_type = 'Effect Size'
        e_name = 'Beta'
        e_name_short = 'β'
        e_estimate = -0.7
        bm_metric_effect = self.create_bm_metric(bm_performance.id,e_type,e_name,e_name_short,e_estimate,'years',0.15,None)
        # Instance
        self.assertTrue(isinstance(bm_metric_effect, BM_Metric))
        # Other methods
        self.assertEqual(bm_metric_effect.display_value(),str(e_estimate))
        self.assertEqual(bm_metric_effect.name_tuple(), (e_name,e_name_short))
        self.assertEqual(bm_metric_effect.__str__(), '{} ({}): {}'.format(e_name,e_name_short,e_estimate))

        # Type "Classification Metric"
        c_type = 'Classification Metric'
        c_name = 'Concordance Statistic'
        c_name_short = 'C-index'
        c_estimate = 0.655
        c_ci = '[0.605,0.667]'
        bm_metric_class = self.create_bm_metric(bm_performance.id,c_type,c_name,c_name_short,c_estimate,'',None,c_ci)
        # Instance
        self.assertTrue(isinstance(bm_metric_class, BM_Metric))
        # Other methods
        self.assertEqual(bm_metric_class.display_value(), str(c_estimate)+' '+c_ci)
        self.assertEqual(bm_metric_class.name_tuple(), (c_name,c_name_short))
        self.assertEqual(bm_metric_class.__str__(), '{} ({}): {} {}'.format(c_name,c_name_short,c_estimate,c_ci))


        # Type "Other Metric"
        o_type = 'Other Metric'
        o_name = 'correlation (r)'
        o_name_short = None
        o_estimate = 0.29
        o_ci = '[0.231,0.349]'
        bm_metric_other = self.create_bm_metric(bm_performance.id,o_type,o_name,o_name_short,o_estimate,'',None,o_ci)
        # Instance
        self.assertTrue(isinstance(bm_metric_other, BM_Metric))
        # Other methods
        self.assertEqual(bm_metric_other.display_value(), str(o_estimate)+' '+o_ci)
        self.assertEqual(bm_metric_other.name_tuple(), (o_name,o_name))
        self.assertEqual(bm_metric_other.__str__(), '{}: {} {}'.format(o_name,o_estimate,o_ci))


        # Performance tests
        perf_effect = bm_performance.effect_sizes_list
        self.assertEqual(len(perf_effect), 1)
        self.assertEqual(perf_effect[0][0][0], e_name)

        perf_class = bm_performance.class_acc_list
        self.assertEqual(len(perf_class), 1)
        self.assertEqual(perf_class[0][0][0], c_name)

        perf_other = bm_performance.othermetrics_list
        self.assertEqual(len(perf_other), 1)
        self.assertEqual(perf_other[0][0][0], o_name)

        perf_dict = bm_performance.performance_metrics
        self.assertEqual(perf_dict['effect_sizes'], [{ 'labels': (e_name,e_name_short), 'value': str(e_estimate) }])
        c_value = bm_metric_class.display_value().replace(',', ', ')
        self.assertEqual(perf_dict['class_acc'], [{ 'labels': (c_name,c_name_short), 'value': c_value }])
        o_value = bm_metric_other.display_value().replace(',', ', ')
        self.assertEqual(perf_dict['othermetrics'], [{ 'labels': (o_name,o_name), 'value': o_value }])


class BM_PerformanceTest(TestCase):
    """ Test the BM_Performance model """
    # Pointer to the database to use
    databases = databases_list

    def create_bm_performance(self, sample, efotrait, cohort, score_id=score_id):
        return BM_Performance.objects.using(benchmark_db).create(sample=sample, efotrait=efotrait, cohort=cohort, score_id=score_id)

    def get_bm_performance(self, sample, efotrait, cohort, score_id=score_id):
        try:
            bm_performance = BM_Performance.objects.using(benchmark_db).get(score_id=score_id, sample=sample, efotrait=efotrait, cohort=cohort)
        except BM_Performance.DoesNotExist:
            bm_performance = self.create_bm_performance(sample, efotrait, cohort)
        return bm_performance


    def test_performance(self):

        # BM_Cohort object
        cohorttest = BM_CohortTest()
        bm_cohort = cohorttest.get_bm_cohort(cohort_name)

        # BM_Sample object
        sampletest = BM_SampleTest()
        bm_sample = sampletest.get_bm_sample(test_sample_number,bm_cohort)

        # BM_EFOTrait object
        efotraittest = BM_EFOTraitTest()
        bm_efotrait = efotraittest.get_bm_efo_trait(efo_id,efo_name,efo_desc)


        bm_performance = self.get_bm_performance(bm_sample, bm_efotrait, bm_cohort)
        # Instance
        self.assertTrue(isinstance(bm_performance, BM_Performance))
        # Variables
        self.assertTrue(isinstance(bm_performance.sample, BM_Sample))
        self.assertTrue(isinstance(bm_performance.cohort, BM_Cohort))
        self.assertTrue(isinstance(bm_performance.efotrait, BM_EFOTrait))
        # Other methods
        self.assertRegex(bm_performance.__str__(), r'^'+efo_id+' | '+score_id+' | '+cohort_name+'$')

        # EFOTrait tests
        bm_efotrait.count_scores
        self.assertEqual(bm_efotrait.bm_data['scores'], [score_id])
        self.assertEqual(bm_efotrait.bm_data['cohorts'], [bm_cohort])
        self.assertEqual(bm_efotrait.bm_data['samples'], [bm_sample.id])
        self.assertEqual(bm_efotrait.bm_data['ancestries'], [bm_sample.ancestry_broad])
        self.assertEqual(bm_efotrait.count_scores, 1)
        self.assertEqual(bm_efotrait.count_cohorts, 1)
        self.assertEqual(bm_efotrait.count_samples, 1)
        self.assertEqual(bm_efotrait.cohorts_list, [bm_cohort])
        self.assertEqual(bm_efotrait.ancestries_list, [bm_sample.ancestry_broad])


class BM_SampleTest(TestCase):
    """ Test the BM_Sample model """
    # Pointer to the database to use
    databases = databases_list

    number = 10
    cases = 6
    controls = 4
    sample_sex = 'Both'
    a_broad = 'European'
    a_free = 'NR'
    a_free_2 = 'Cambridgeshire'
    a_country = 'U.K.'
    a_additional = 'White European'

    cohort_name = 'UKB'
    #cohorttest = BM_CohortTest()
    #bm_cohort = cohorttest.create_bm_cohort(cohort_name)

    #for c in BM_Cohort.objects.using(benchmark_db).all():
    #    print("Cohort: "+str(c.id)+" | "+c.name_short)
    def get_bm_sample(self,sample_number,bm_cohort):
        try:
            bm_sample = BM_Sample.objects.using(benchmark_db).get(sample_number=sample_number, cohort=bm_cohort)
        except BM_Sample.DoesNotExist:
            bm_sample = self.create_bm_sample(bm_cohort, sample_number=sample_number)
        return bm_sample

    def create_bm_sample(self, cohort, sample_number=number, broad=broad_ancestry):
        return BM_Sample.objects.using(benchmark_db).create(sample_number=sample_number,cohort=cohort, ancestry_broad=broad)

    def create_bm_sample_numbers(self, cohort, sample_number=number,sample_cases=cases,sample_controls=controls,sample_sex=sample_sex):
        return BM_Sample.objects.using(benchmark_db).create(sample_number=sample_number,sample_cases=sample_cases,sample_controls=sample_controls,sample_sex=sample_sex,cohort=cohort)

    def create_bm_sample_ancestry(self, cohort, sample_number=number,broad=a_broad,free=a_free,country=a_country,additional=a_additional):
        return BM_Sample.objects.using(benchmark_db).create(
            sample_number=sample_number,
            ancestry_broad=broad,
            ancestry_free=free,
            ancestry_country=country,
            ancestry_additional=additional,
            cohort=cohort
        )


    def test_sample(self):

        cohorttest = BM_CohortTest()
        bm_cohort = cohorttest.get_bm_cohort(cohort_name)

        ## Simple Sample object
        bm_sample_1 = self.create_bm_sample(bm_cohort,test_sample_number)
        # Instance
        self.assertTrue(isinstance(bm_sample_1, BM_Sample))
        # Variables
        self.assertEqual(bm_sample_1.sample_number, test_sample_number)
        # Other methods
        self.assertRegex(bm_sample_1.__str__(), r'^Sample:\s\d+$')
        self.assertIsNotNone(bm_sample_1.display_samples_for_table)

        ## Sample object with numbers
        bm_sample_2 = self.create_bm_sample_numbers(bm_cohort)
        # Instance
        self.assertTrue(isinstance(bm_sample_2, BM_Sample))
        # Variables
        self.assertEqual(bm_sample_2.sample_number, self.number)
        self.assertEqual(bm_sample_2.sample_cases, self.cases)
        self.assertEqual(bm_sample_2.sample_controls, self.controls)
        self.assertEqual(bm_sample_2.sample_sex, self.sample_sex)
        self.assertEqual(bm_sample_2.sample_cases_percent, round((self.cases/self.number)*100,2))
        # Other methods
        self.assertIsNotNone(bm_sample_2.sample_cases_percent)
        self.assertIsNotNone(bm_sample_2.display_samples_for_table())
        self.assertIsNotNone(bm_sample_2.display_samples_for_table(True))

        ## Sample object with ancestry
        bm_sample_3 = self.create_bm_sample_ancestry(bm_cohort)
        bm_sample_3.sample_cases = None
        bm_sample_3.sample_controls = None
        # Instance
        self.assertTrue(isinstance(bm_sample_3, BM_Sample))
        # Variables
        self.assertEqual(bm_sample_3.ancestry_broad, self.a_broad)
        self.assertEqual(bm_sample_3.ancestry_free, self.a_free)
        self.assertEqual(bm_sample_3.ancestry_country, self.a_country)
        self.assertEqual(bm_sample_3.ancestry_additional, self.a_additional)
        # Other methods
        self.assertEqual(bm_sample_3.display_ancestry, self.a_broad)
        self.assertEqual(bm_sample_3.display_ancestry_inline, self.a_broad)
        bm_sample_3.ancestry_free = 'Cambridgeshire'
        self.assertEqual(bm_sample_3.display_ancestry, '{}<br/>({})'.format(self.a_broad, self.a_free_2))
        self.assertEqual(bm_sample_3.display_ancestry_inline, '{} ({})'.format(self.a_broad, self.a_free_2))
        self.assertIsNone(bm_sample_3.sample_cases)
        self.assertIsNone(bm_sample_3.sample_cases_percent)
        self.assertIsNone(bm_sample_3.sample_controls)
        self.assertEqual(bm_sample_3.display_samples_for_table(), str(self.number)+' individuals')
