import pandas as pd
import csv
from curation.imports.study import StudyImport
from curation.imports.scoring_file import ScoringFileUpdate, VariantPositionsQC
from curation_tracker.models import CurationPublicationAnnotation


curation_tracker = 'curation_tracker'

class CurationImport():
    '''
    Class responsible to import study metadata from a list of spreadsheet files.
    It can be split in 3 steps:
    - Parse the spreadsheet files and store temporary the data
    - Import the stored data into the database
    - Update the corresponding scoring files with a new header
    '''

    failed_studies = {}

    def __init__(self, data_path, studies_list, curation_status_by_default, scoringfiles_format_version, skip_scoringfiles, skip_curationtracker, variant_positions_qc_config, reported_traits_dict_file:str):
        self.curation2schema = pd.read_excel(data_path['template_schema'], sheet_name='Curation', index_col=0)
        self.curation2schema_scoring = pd.read_excel(data_path['scoring_schema'], sheet_name='Columns', index_col=0)


        self.studies_list = studies_list
        self.studies_path = data_path['studies_dir']
        self.new_scoring_path = data_path['scoring_dir']
        self.scoringfiles_format_version = scoringfiles_format_version
        self.skip_scoringfiles = skip_scoringfiles
        self.skip_curationtracker = skip_curationtracker

        self.curation_status_by_default = curation_status_by_default
        self.variant_positions_qc_config = variant_positions_qc_config

        # Reading the reported-traits dictionary file
        try:
            with open(reported_traits_dict_file, mode='r') as infile:
                reader = csv.DictReader(infile, delimiter='\t')
                self.reported_traits_cleaner = {row['trait_reported']: row['corrected'] for row in reader}
        except FileNotFoundError:
            print('ERROR: Could not find \'reported_traits_dict_file\'')
            self.reported_traits_cleaner = {}

        self.step = 1
        self.steps_total = 2
        if self.skip_scoringfiles == False:
            self.steps_total = self.steps_total + 1
        if self.skip_curationtracker == False:
            self.steps_total = self.steps_total + 1
        if self.variant_positions_qc_config['skip'] == False:
            self.steps_total = self.steps_total + 1


    def global_report(self):
        ''' Global reports of the studies parsing/import and the scoring files updates '''
        studies_count = len(self.studies_list)
        import_success = studies_count - len(self.failed_studies.keys())
        print('\n=======================================================\n')
        print('#------------------------#')
        print('# End of script - Report #')
        print('#------------------------#')
        print(f'Successful imports: {import_success}/{studies_count}')
        if self.failed_studies:
            print(f'Failed imports:')
            for study,error_type in self.failed_studies.items():
                print(f'- {study}: {error_type}')
        print('\n')


    def run_curation_import(self):
        '''
        Method to run the curation import processes for each study:
        - parse study data
        - import study data into the database via the Django "catalog" models
        - update the scoring files by adding a header
        - print a global report for each study
        '''
        for study_data in self.studies_list:

            ## Parsing ##
            self.step = 1
            study_import = StudyImport(study_data, self.studies_path, self.curation2schema, self.curation_status_by_default, self.reported_traits_cleaner)
            study_import.print_title()
            print(f'==> Step {self.step}/{self.steps_total}: Parsing study data')
            study_import.parse_curation_data()

            ## Import ##
            self.step += 1
            print('\n----------------------------------\n')
            print(f'==> Step {self.step}/{self.steps_total}: Importing study data')
            study_import.import_curation_data()
            if study_import.has_failed:
                self.failed_studies[study_import.study_name] = 'import error'
                continue

            ## Scoring files ##
            if self.skip_scoringfiles == False:
                self.step += 1
                print('\n----------------------------------\n')
                print(f'==> Step {self.step}/{self.steps_total}: Add header to the Scoring file(s)')
                if study_import.study_scores:
                    for score_id, score in study_import.study_scores.items():
                        scoring_file_update = ScoringFileUpdate(score, study_import.study_path, self.new_scoring_path, self.curation2schema_scoring, self.scoringfiles_format_version)
                        is_failed = scoring_file_update.update_scoring_file()
                        if is_failed == True:
                            self.failed_studies[study_import.study_name] = 'scoring file error'
                            continue
                else:
                    print("  > No scores for this study, therefore no scoring files")
                if study_import.study_name in self.failed_studies.keys():
                    continue

            ## Variant positions QC ##
            if not self.variant_positions_qc_config['skip']:
                self.step += 1
                print('\n----------------------------------\n')
                print(f'==> Step {self.step}/{self.steps_total}: QC of the variant positions of the Scoring file(s)')
                if study_import.study_scores:
                    for score_id, score in study_import.study_scores.items():
                        print(f'SCORE: {score.id}')
                        variant_pos_qc = VariantPositionsQC(score, self.new_scoring_path, self.variant_positions_qc_config)
                        is_failed = variant_pos_qc.qc_variant_positions(
                            report_func=lambda msg: print(f'  > {msg}'),
                            error_func=lambda msg: print(f'ERROR: {msg}!')
                        )
                        if is_failed:
                            self.failed_studies[study_import.study_name] = 'scoring file error'
                            continue
                else:
                    print("  > No scores for this study, therefore no scoring files")
                if study_import.study_name in self.failed_studies.keys():
                    continue

            ## Update Curation Tracker ##
            if self.skip_curationtracker == False:
                self.step += 1
                print('\n----------------------------------\n')
                print(f'==> Step {self.step}/{self.steps_total}: Update the study status in the Curation Tracker')
                curation_pub = None
                if study_import.study_publication.doi:
                    try:
                        curation_pub = CurationPublicationAnnotation.objects.using(curation_tracker).get(doi=study_import.study_publication.doi)
                        print("  > Study found using the publication DOI")
                    except CurationPublicationAnnotation.DoesNotExist:
                        print("  ! Study NOT found using the publication DOI")

                if curation_pub == None:
                    try:
                        curation_pub = CurationPublicationAnnotation.objects.using(curation_tracker).get(study_name=study_import.study_name)
                        print("  > Study found in Curation Tracker, using the study name")
                    except CurationPublicationAnnotation.DoesNotExist:
                        print("  > Can't find/retrieve the study in the Curation Tracker to update its status")
                        self.failed_studies[study_import.study_name] = 'curation tracker error'

                if curation_pub != None:
                    curation_pub.curation_status = 'Imported - Awaiting Release'
                    curation_pub.save()
                    print("  > Curation status updated in the Curation Tracker")

        self.global_report()
