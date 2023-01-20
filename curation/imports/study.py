# import gzip
# import pandas as pd
# import numpy as np
from curation.template_parser import *
from catalog.models import *


class StudyImport():
    '''
    Class generating running the parsing of the input file (spreadsheet), storing the parsed data
    into temporary objects ans then importing the data into the database, via the Django models.
    '''

    data_obj = [
        ('performance', 'num', Performance),
        ('sampleset', 'num', SampleSet),
        ('sample', 'id', Sample)
    ]

    def __init__(self, study_data, studies_dir, curation_schema, curation_status_by_default):
        self.study_name = study_data['name']

        if not studies_dir.endswith('/'):
            studies_dir += '/'
        self.study_path = f'{studies_dir}{self.study_name}'

        self.study_license = None
        if 'license' in study_data:
            self.study_license = study_data['license']

        self.study_status = None
        if 'status' in study_data:
            self.study_status = study_data['status']

        self.curation_schema = curation_schema

        self.default_curation_status = curation_status_by_default

        self.data_ids = {
            'performance': [],
            'sampleset': [],
            'sample': []
        }

        self.study_scores = {}
        self.existing_scores = []

        self.import_warnings = []
        self.failed_data_import = []
        self.has_failed = False


    def print_title(self):
        ''' Print the study name '''
        title = f'Study: {self.study_name}'
        border = '===='
        for i in range(len(title)):
            border += '='
        print(f'\n\n{border}\n# Study: {self.study_name} #\n{border}')
        if self.study_status:
            print(f'Curation status: {self.study_status}\n')


    def parse_curation_data(self):
        '''
        Read the spreadsheet file and run the different parsers.
        The parsed data is stored in into a CurationTemplate object
        '''
        self.study = CurationTemplate()
        self.study.file_loc  = f'{self.study_path}/{self.study_name}.xlsx'
        self.study.table_mapschema = self.curation_schema
        self.study.read_curation()
        # Extract data from the different spreadsheets
        self.study.extract_cohorts()
        self.study.extract_publication(self.study_status)
        self.study.extract_scores(self.study_license)
        self.study.extract_samples()
        self.study.extract_performances()


    def import_curation_data(self):
        '''
        Run the data import from the data collected by the parsers.
        It also print the import reports and errors
        '''
        self.import_publication_model()
        self.import_score_models()
        self.import_gwas_dev_samples()
        self.remove_existing_performance_metrics()
        self.import_samplesets()
        self.import_performance_metrics()

        # Print import warnings
        if len(self.import_warnings):
            print('\n>>>> Import information <<<<')
            print('  - '+'\n  - '.join(self.import_warnings))

        # Remove entries if the import failed
        if len(self.failed_data_import):
            self.has_failed = True
            print('\n**** ERROR: Import failed! ****')
            print('  - '+'\n  - '.join(self.failed_data_import))
            for obj in self.data_obj:
                ids = self.data_ids[obj[0]]
                if len(ids):
                    col_condition = obj[1] + '__in'
                    obj[2].objects.filter(**{ col_condition: ids}).delete()
                    print(f'  > DELETED {obj[0]} (column "{obj[1]}") : {ids}')


    def import_publication_model(self):
        ''' Import the Publication data if the Publication is not yet in the database. '''
        if self.study.parsed_publication.model:
            self.study_publication = self.study.parsed_publication.model
        else:
            try:
                self.study_publication = Publication.objects.get(**self.study.parsed_publication.data)
            except Publication.DoesNotExist:
                self.study_publication = self.study.parsed_publication.create_publication_model()
                # Set publication curation status
                if not self.study_status:
                    self.study_publication.curation_status = self.default_curation_status
                    self.study_publication.save()


    def import_score_models(self):
        ''' Import the Score data if the Score is not yet in the database. '''
        print('> Import Scores')
        for score_id, score_data in self.study.parsed_scores.items():
            # Check if Score model already exists
            try:
                score = Score.objects.get(name=score_data.data['name'],publication__id=self.study_publication.id)
                self.import_warnings.append(f'Existing Score: {score.id} ({score_id})')
                self.existing_scores.append(score.id)
            # Create Score model
            except Score.DoesNotExist:
                score = score_data.create_score_model(self.study_publication)
                self.import_warnings.append(f'New Score: {score.id} ({score_id})')
            self.study_scores[score_id] = score


    def import_gwas_dev_samples(self):
        ''' Import the GWAS and Dev/Training Samples and attach them the associated Score(s) '''
        print('> Import GWAS and Dev/Training Samples')
        try:
            for x in self.study.parsed_samples_scores:
                scores = []
                sample_type = x[0][1]
                # Extract scores
                for s in x[0][0].split(','):
                    if s.strip() in self.study_scores:
                        scores.append(self.study_scores[s.strip()])
                    else:
                        self.import_warnings.append(f'{s.strip()} is not found in the saved scores list!!!')
                samples = x[1]
                for score in scores:
                    print(f'SCORE: {score.id} - {x[0]}')
                    for sample in samples:
                        sample_model_exist = sample.sample_model_exist()
                        if 'source_GWAS_catalog' in sample.data:
                            source = sample.data['source_GWAS_catalog']
                        else:
                            source = 'Not GWAS'
                        # Existing sample
                        if sample_model_exist:
                            sample_model = sample_model_exist
                            self.import_warnings.append(f'Sample "{x[0][0]}" ({x[0][1]}) already exist in the Database')
                        # New sample
                        else:
                            sample_model = sample.create_sample_model()
                        if sample_type == 'GWAS/Variant associations':
                            score.samples_variants.add(sample_model)
                        elif sample_type == 'Score development':
                            score.samples_training.add(sample_model)
                        else:
                            self.import_warnings.append('ERROR: Unclear how to add samples')
        except Exception as e:
            self.failed_data_import.append(f'GWAS & Dev/Testing Sample: {e}')


    def remove_existing_performance_metrics(self):
        '''
        Check if the Performance Metrics already exist in the DB
        If they exist, we delete them (including the associated SampleSet and Samples)
        '''
        print('> Remove existing Performance Metrics')
        try:
            data_types = ('performance','sampleset','sample')
            data2delete = { k:set() for k in data_types }
            model2delete = {'performance': Performance, 'sampleset': SampleSet, 'sample': Sample}
            # Loop over the parsed performances
            for x in self.study.parsed_performances:
                i, performance = x
                # Find Score from the Score spreadsheet
                if i[0] in self.study_scores:
                    score = self.study_scores[i[0]]
                # Find existing Score in the database (e.g. PGS000001)
                else:
                    try:
                        score = Score.objects.get(id__iexact=i[0])
                    except Score.DoesNotExist:
                        self.failed_data_import.append(f'Performance Metric: can\'t find the Score {i[0]} in the database')
                        continue
                performances = Performance.objects.filter(publication=self.study_publication, score=score)

                # List objects to delete
                for performance in performances:
                    sampleset = performance.sampleset
                    samples = sampleset.samples.all()
                    # Store the objects to delete
                    data2delete['performance'].add(performance)
                    data2delete['sampleset'].add(sampleset)
                    for sample in samples:
                        data2delete['sample'].add(sample)

            # Delete stored objects in "bulk"
            for data_type in data_types:
                data_list = list(data2delete[data_type])
                if data_list:
                    ids = [str(x.id) for x in data_list]
                    self.import_warnings.append(f'DELETE existing {data_type}(s) [ids]: {", ".join(ids)}')
                    # Delete associated Metrics (only for Performance data)
                    if data_type == 'performance':
                        num_ids = [str(x.num) for x in data_list]
                        Metric.objects.filter(performance_id__in=num_ids).delete()
                    # Delete entries
                    model2delete[data_type].objects.filter(id__in=ids).delete()

        except Exception as e:
            self.failed_data_import.append(f'Check existing Performance Metric: {e}')


    def import_samplesets(self):
        ''' Import Test (Evaluation) Samples and Sample Sets '''
        print('> Import Sample Sets')
        self.study_samplesets = {}
        try:
            for x in self.study.parsed_samples_testing:
                test_name, sample_list = x

                # Create the SampleSet object
                sampleset_model = SampleSet()
                sampleset_model.set_ids(next_PSS_num())
                sampleset_model.save()
                self.data_ids['sampleset'].append(sampleset_model.num)

                # Create Samples and store them in a list
                samples_for_sampleset = []
                sampleset_name = ''
                for sample_test in sample_list:
                    sample_model = sample_test.create_sample_model()
                    self.data_ids['sample'].append(sample_model.id)
                    samples_for_sampleset.append(sample_model)
                    sampleset_name = sample_test.sampleset_name

                # Add the Sample(s) to the SampleSet
                sampleset_model.samples.set(samples_for_sampleset)
                sampleset_model.name = sampleset_name
                sampleset_model.save()

                # Add the SampleSet to the list of SampleSets for the study
                self.study_samplesets[test_name] = sampleset_model

        except Exception as e:
            self.failed_data_import.append(f'SampleSet & Evaluation Sample: {e}')


    def import_performance_metrics(self):
        ''' Import the Performance and the associated Metric(s) '''
        print('> Import the Performance Metrics')
        metric_models = []
        try:
            for x in self.study.parsed_performances:
                i, performance = x
                # Find Score from the Score spreadsheet
                if i[0] in self.study_scores:
                    current_score = self.study_scores[i[0]]
                # Find existing Score in the database (e.g. PGS000001)
                else:
                    try:
                        current_score = Score.objects.get(id__iexact=i[0])
                    except Score.DoesNotExist:
                        self.failed_data_import.append(f'Performance Metric: can\'t find the Score {i[0]} in the database')
                        continue

                related_SampleSet = self.study_samplesets[i[1]]

                if len(performance.metrics) == 0:
                    self.failed_data_import.append(f"Performance Metric - {current_score.id}: ({current_score.name} - {related_SampleSet.name} - {performance.data['phenotyping_reported']}): missing/wrong-formatted Metric data")

                #  Create the Performance and the associated Metric(s)
                study_performance = performance.create_performance_model(publication=self.study_publication, score=current_score, sampleset=related_SampleSet)
                if study_performance:
                    self.import_warnings.append(f'New Performance Metric: {study_performance.id} & new Sample Set: {study_performance.sampleset.id}')
                    self.data_ids['performance'].append(study_performance.num)
                else:
                    self.import_warnings.append(f'Performance Metric not created because of an issue while creating it.')
                    if 'error' in performance.report['import']:
                        msg = ', '.join(performance.report['import']['error'])
                        self.failed_data_import.append(f'Performance Metric: {msg}')
                    continue
                # Add the performance metrics to the list
                metric_models.extend(performance.metric_models)

            # Insert Metric data in bulk
            metrics_list = Metric.objects.bulk_create(metric_models)

        except Exception as e:
            self.failed_data_import.append(f'Performance Metric: {e}')
