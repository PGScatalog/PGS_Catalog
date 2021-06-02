from django.test import TestCase
from curation.imports.curation import CurationImport
from catalog.models import *



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

default_curation_status = 'IP'

skip_scorefiles = True

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
        curation_import = CurationImport(curation_directories, study_names_list, default_curation_status, skip_scorefiles)
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
