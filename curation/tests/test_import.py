from django.test import TestCase
from curation.imports.curation import CurationImport
from catalog.models import *
from curation.imports.reported_trait_cleaner import ReportedTraitCleaner

# Configuration
curation_directories = {
    'template_schema': './curation/templates/TemplateColumns2Models.xlsx',
    'scoring_schema': './curation/templates/ScoringFileSchema.xlsx',
    'studies_dir': './curation/tests/test_files',
    'scoring_dir': ''
}

study_names_list = [
    { 'name': 'FirstTest2021' , 'license': 'Not the default license'},
    { 'name': 'SecondTest2021' },
    { 'name': 'ThirdTest2021', 'status': 'E' }
]

scoringfiles_format_version = '2.0'

default_curation_status = 'IP'

skip_scorefiles = True

skip_curationtracker = True

variant_positions_qc_config = {
    'skip': True
}

reported_traits_cleaning_config = {
    'replacement_file': './curation/tests/test_files/reported_traits_dict.tsv'
}

# Test values
data_counts = {
    'publication': len(study_names_list),
    'score': 3,
    'trait': 3,
    'cohort': 7,
    'performance': 5,
    'sampleset': 5
}

class ImportTest(TestCase):

    def run_import(self):
        # Main script
        reported_trait_cleaner = ReportedTraitCleaner(reported_traits_replacement_file=reported_traits_cleaning_config['replacement_file'])
        curation_import = CurationImport(
            data_path=curation_directories, studies_list=study_names_list, curation_status_by_default=default_curation_status,
            scoringfiles_format_version=scoringfiles_format_version, skip_scoringfiles=skip_scorefiles,
            skip_curationtracker=skip_curationtracker, variant_positions_qc_config=variant_positions_qc_config,
            reported_traits_cleaner=reported_trait_cleaner)
        curation_import.run_curation_import()


    def test_import(self):
        ## Run the import ##
        self.run_import()


        ## Counting tests ##
        # Publication
        pubs = Publication.objects.all()
        self.assertEqual(pubs.count(), data_counts['publication'])

        # Score
        scores = Score.objects.all()
        self.assertEqual(scores.count(), data_counts['score'])

        # Trait
        traits = EFOTrait.objects.all()
        self.assertEqual(traits.count(), data_counts['trait'])

        # Cohort
        cohorts = Cohort.objects.all()
        self.assertEqual(cohorts.count(), data_counts['cohort'])

        # Performance
        performances = Performance.objects.all()
        self.assertEqual(performances.count(), data_counts['performance'])

        # SampleSet
        samplesets = SampleSet.objects.all()
        self.assertEqual(samplesets.count(), data_counts['sampleset'])


        ## Other tests ##
        for id, study in enumerate(study_names_list, start=1):

            # Status
            if 'status' in study:
                status = study['status']
            else:
                status = default_curation_status

            try:
                publication = Publication.objects.get(num=id)
                self.assertIsNotNone(publication.id)
                self.assertIsNotNone(publication.firstauthor)
                self.assertEqual(publication.curation_status, status)
            except Publication.DoesNotExist:
                print(f'Test - Can\'t find a Publication with num={id}')
                continue

            # Scores
            scores = Score.objects.filter(publication=publication)
            for score in scores:
                self.assertIsNotNone(score.id)
                self.assertIsNotNone(score.name)
                # License
                if 'license' in study:
                    license = study['license']
                    self.assertEqual(score.license, license)

                # Performance
                performances = Performance.objects.filter(score=score, publication=publication)
                self.assertGreater(performances.count(), 0)

                # Metrics
                for performance in performances:
                    metrics = Metric.objects.filter(performance=performance)
                    self.assertGreater(metrics.count(), 0)

        ## Reported trait cleaning test ##
        coffee_score = Score.objects.get(name='PGS_test1')
        self.assertEqual(coffee_score.trait_reported, 'Caffeine consumption')
