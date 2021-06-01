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
        ''' Import the Scofe data if the Score is not yet in the database. '''
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
        try:
            for x in self.study.parsed_samples_scores:
                scores = []
                # Extract scores
                for s in x[0][0].split(','):
                    if s.strip() in self.study_scores:
                        scores.append(self.study_scores[s.strip()])
                    else:
                        self.import_warnings.append(f'{s.strip()} is not found in the saved scores list!!!')
                samples = x[1]
                for score in scores:
                    for sample in samples:
                        sample_model_exist = False
                        if score.id in self.existing_scores:
                            sample_model_exist = sample.sample_model_exist()
                        # New sample
                        if not sample_model_exist:
                            sample_model = sample.create_sample_model()
                            if x[0][1] == 'GWAS/Variant associations':
                                score.samples_variants.add(sample_model)
                            elif x[0][1] == 'Score development':
                                score.samples_training.add(sample_model)
                            else:
                                self.import_warnings.append('ERROR: Unclear how to add samples')
                        else:
                            self.import_warnings.append(f'Sample "{x[0][0]}" ({x[0][1]}) already exist in the Database')
        except Exception as e:
            self.failed_data_import.append(f'GWAS & Dev/Testing Sample: {e}')


    def remove_existing_performance_metrics(self):
        '''
        Check if the Performance Metrics already exist in the DB
        If they exist, we delete them (including the associated SampleSet and Samples)
        '''
        try:
            data2delete = {'performance': set(), 'sampleset': set(), 'sample': set()}
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
                
                for performance in performances:
                    sampleset = performance.sampleset
                    samples = sampleset.samples.all()
                    # Store the objects to delete
                    data2delete['performance'].add(performance)
                    data2delete['sampleset'].add(sampleset)
                    for sample in samples:
                        data2delete['sample'].add(sample)
            # Delete stored objects
            for data_type in ('performance','sampleset','sample'):
                data_list = list(data2delete[data_type])
                if data_list:
                    self.import_warnings.append(f'DELETE existing {data_type}(s) [ids]: {", ".join([str(x.id) for x in data_list])}')
                    for entry in data_list:
                        entry.delete()

        except Exception as e:
            self.failed_data_import.append(f'Check existing Performance Metric: {e}')


    def import_samplesets(self):
        ''' Import Test (Evaluation) Samples and Sample Sets '''
        self.study_samplesets = {}
        try:
            for x in self.study.parsed_samples_testing:
                test_name, sample_list = x

                samples_for_sampleset = []

                # Create Samples and store them in a list
                for sample_test in sample_list:
                    sample_model = sample_test.create_sample_model()
                    self.data_ids['sample'].append(sample_model.id)
                    samples_for_sampleset.append(sample_model)
                    
                # Create the SampleSet object
                sampleset_model = SampleSet()
                sampleset_model.set_ids(next_PSS_num())
                sampleset_model.save()
                self.data_ids['sampleset'].append(sampleset_model.num)

                # Add the Sample(s) to the SampleSet
                for sample in samples_for_sampleset:
                    sampleset_model.samples.add(sample)
                    sampleset_model.save()

                self.study_samplesets[test_name] = sampleset_model
        except Exception as e:
            self.failed_data_import.append(f'SampleSet & Evaluation Sample: {e}')


    def import_performance_metrics(self):
        ''' Import the Performance and the associated Metric(s) '''
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
        except Exception as e:
            self.failed_data_import.append(f'Performance Metric: {e}')
