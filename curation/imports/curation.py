import pandas as pd
from curation.imports.study import StudyImport
from curation.imports.scoring_file import ScoringFileUpdate


class CurationImport():
    '''
    Class responsible to import study metadata from a list of spreadsheet files.
    It can be split in 3 steps:
    - Parse the spreadsheet files and store temporary the data
    - Import the stored data into the database
    - Update the corresponding scoring files with a new header
    '''

    failed_studies = {}

    def __init__(self, data_path, studies_list, curation_status_by_default, scoringfiles_format_version, skip_scoringfiles):
        self.curation2schema = pd.read_excel(data_path['template_schema'], sheet_name='Curation', index_col=0)
        self.curation2schema_scoring = pd.read_excel(data_path['scoring_schema'], sheet_name='Columns', index_col=0)


        self.studies_list = studies_list
        self.studies_path = data_path['studies_dir']
        self.new_scoring_path = data_path['scoring_dir']
        self.scoringfiles_format_version = scoringfiles_format_version
        self.skip_scoringfiles = skip_scoringfiles

        self.curation_status_by_default = curation_status_by_default

        self.steps_count = 2
        if self.skip_scoringfiles == False:
            self.steps_count = 3


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
            study_import = StudyImport(study_data, self.studies_path, self.curation2schema, self.curation_status_by_default)
            study_import.print_title()
            print(f'==> Step 1/{self.steps_count}: Parsing study data')
            study_import.parse_curation_data()
            if study_import.has_failed:
                self.failed_studies[study_import.study_name] = 'import error'
                continue

            ## Import ##
            print('\n----------------------------------\n')
            print(f'==> Step 2/{self.steps_count}: Importing study data')
            study_import.import_curation_data()
            if study_import.has_failed:
                self.failed_studies[study_import.study_name] = 'import error'
                continue

            ## Scoring files ##
            if self.skip_scoringfiles == False:
                print('\n----------------------------------\n')
                print(f'==> Step 3/{self.steps_count}: Add header to the Scoring file(s)')
                if study_import.study_scores:
                    for score_id, score in study_import.study_scores.items():
                        scoring_file_update = ScoringFileUpdate(score, study_import.study_path, self.new_scoring_path, self.curation2schema_scoring, self.scoringfiles_format_version)
                        is_failed = scoring_file_update.update_scoring_file()
                        if is_failed == True:
                            self.failed_studies[study_import.study_name] = 'scoring file error'
                            print(f"  /!\ Updated Scoring File couldn't be generated!")
                else:
                    print("  > No scores for this study, therefore no scoring files")

        self.global_report()
