from cmath import nan
import pandas as pd
import numpy as np
import requests
import re
from datetime import date
from catalog.models import *
from curation.parsers.cohort import CohortData
from curation.parsers.publication import PublicationData
from curation.parsers.score import ScoreData
from curation.parsers.sample import SampleData
from curation.parsers.performance import PerformanceData


class CurationTemplate():
    def __init__(self):
        self.file_loc = None
        self.parsed_publication = None
        self.parsed_scores = {}
        self.parsed_cohorts = {}
        self.parsed_samples_scores = []
        self.parsed_samples_testing = []
        self.parsed_performances = []
        self.table_mapschema = None
        self.spreadsheet_names = {}
        self.report = { 'error': {}, 'warning': {}, 'import': {} }

    def get_spreadsheet_names(self):
        ''' Mapping between Django catalog models and speadsheet names '''
        for s_name, s_content in self.table_mapschema.iterrows():
            # Fetch model
            s_model = s_content[1]
            if s_model not in self.spreadsheet_names:
                self.spreadsheet_names[s_model] = s_name


    def read_curation(self):
        ''' Read metadata file and store the spreadsheets into pandas DataFrames. '''

        self.get_spreadsheet_names()

        loc_excel = self.file_loc
        if loc_excel != None:
            self.table_publication =  pd.read_excel(loc_excel, sheet_name=self.spreadsheet_names['Publication'], header=0, index_col=0)

            self.table_scores = pd.read_excel(loc_excel, sheet_name=self.spreadsheet_names['Score'], header=[0, 1], index_col=0)

            self.table_samples = pd.read_excel(loc_excel, sheet_name=self.spreadsheet_names['Sample'], header=0)

            # GWAS and Dev/Training Samples
            self.table_samples_scores = self.table_samples[[x.startswith('Test') is False for x in self.table_samples.iloc[:, 1]]]
            # Index on columns "Score Name(s)" & "Study Stage"
            self.table_samples_scores.set_index(list(self.table_samples_scores.columns[[0, 1]]), inplace = True)

            # Testing (Evaluation) Samples
            self.table_samples_testing = self.table_samples[[x.startswith('Test') for x in self.table_samples.iloc[:, 1]]]
            # Index on column "Sample Set ID"
            self.table_samples_testing.set_index(list(self.table_samples_testing.columns[[2]]), inplace=True)

            self.table_performances = pd.read_excel(loc_excel, sheet_name=self.spreadsheet_names['Performance'], header=[0,1], index_col=[0, 1])

            self.table_cohorts = pd.read_excel(loc_excel, sheet_name=self.spreadsheet_names['Cohort'], header=0, index_col=0)
        else:
            self.report_error('Global', "Missing spreadsheet file!")


    def extract_cohorts(self):
        ''' Extract cohort information and store it into CohortData objects. '''
        spreadsheet_name = self.spreadsheet_names['Cohort']
        current_schema = self.table_mapschema.loc[spreadsheet_name].set_index('Column')
        # Loop throught the rows
        for cohort_name, cohort_info in self.table_cohorts.iterrows():
            if type(cohort_name) != str:
                continue
            cohort_long_name = cohort_name
            cohort_others_name = None
            # Loop throught the columns
            for col, val in cohort_info.items():
                if col in current_schema.index:
                    if pd.isnull(val) == False:
                        field = current_schema.loc[col, 'Field']
                        if field == 'name_full':
                            cohort_long_name = val
                        elif field == 'name_others':
                            cohort_others_name = val

            parsed_cohort = CohortData(cohort_name,cohort_long_name,cohort_others_name,spreadsheet_name)
            cohort_id = cohort_name.upper()
            if cohort_id in self.parsed_cohorts:
                self.report_warning(spreadsheet_name, f'Ambiguity found in the Cohort spreadsheet: the cohort ID "{cohort_name}" has been found more than once!')
            self.parsed_cohorts[cohort_id] = parsed_cohort
            self.update_report(parsed_cohort)


    def extract_publication(self,curation_status=None):
        ''' Extract publication information, fetch extra information via EuropePMC REST API and store it into a PublicationData object. '''
        spreadsheet_name = self.spreadsheet_names['Publication']
        pinfo = self.table_publication.iloc[0]
        c_doi = pinfo['doi']
        if type(c_doi) == str:
            c_doi = c_doi.strip()
            if c_doi.startswith('https'):
                c_doi = c_doi.replace('https://doi.org/','')
            elif c_doi.startswith('http'):
                c_doi = c_doi.replace('http://doi.org/','')
        c_PMID = pinfo[0]
        publication = None
        new_publication = True
        # If there is a DOI or PMID
        if type(c_doi) == str or type(c_PMID) == int:
            if type(c_doi) == str:
                # Check if this is already in the DB
                try:
                    publication = Publication.objects.get(doi__iexact=c_doi)
                    c_doi = publication.doi
                    c_PMID = publication.PMID
                    new_publication = False
                    print("  > Existing publication found in the database\n")
                except Publication.DoesNotExist:
                    print(f'  > New publication ({c_doi}) for the Catalog\n')
            elif type(c_PMID) == int:
                # Check if this is already in the DB
                try:
                    publication = Publication.objects.get(PMID=c_PMID)
                    c_doi = publication.doi
                    c_PMID = publication.PMID
                    new_publication = False
                    print("  > Existing publication found in the database\n")
                except Publication.DoesNotExist:
                    print(f'  > New publication (PMID:{c_PMID}) for the Catalog\n')

            parsed_publication = PublicationData(self.table_publication,spreadsheet_name,c_doi,c_PMID,publication)

            # Fetch the publication information from EuropePMC
            if not publication:
                parsed_publication.get_publication_information()

        # Create the object from the Spreadsheet only
        else:
            parsed_publication = PublicationData(self.table_publication,spreadsheet_name)
            current_schema = self.table_mapschema.loc[spreadsheet_name].set_index('Column')
            previous_field = None
            # Loop throught the columns
            for col, val in pinfo.items():
                if val and col in current_schema.index:
                    field = current_schema.loc[col][1]
                    if type(val) == str or type(val) == int:
                        # Add first author initials
                        if previous_field == 'firstauthor':
                            parsed_publication.data['firstauthor'] = parsed_publication.data['firstauthor']+' '+val
                        else:
                            parsed_publication.add_data(field, val)
                    previous_field = field
            if 'date_publication' not in parsed_publication.data:
                parsed_publication.add_data('date_publication',date.today())
            parsed_publication

        if new_publication == True:
            parsed_publication.add_curation_notes()
            parsed_publication.add_curation_status(curation_status)
        self.parsed_publication = parsed_publication
        self.update_report(self.parsed_publication)


    def extract_scores(self, license=None):
        ''' Extract score information and store it into one or several ScoreData objects. '''
        model = 'Score'
        spreadsheet_name = self.spreadsheet_names[model]
        current_schema = self.table_mapschema.loc[spreadsheet_name].set_index('Column')
        # Loop throught the rows (i.e. score)
        for score_name, score_info in self.table_scores.iterrows():
            parsed_score = ScoreData(score_name,spreadsheet_name)
            if license:
                parsed_score.add_data('license', license)
            # Loop throught the columns
            for col, val in score_info.items():
                if pd.isnull(val) is False:
                    # Map to schema
                    m, f = self.get_model_field_from_schema(col,current_schema)

                    # Add to ScoreData if it's from the Score model
                    if m == model:
                        if f == 'trait_efo':
                            efo_list = val.split(',')
                            parsed_score.add_data(f, efo_list)
                        else:
                            parsed_score.add_data(f, val)
            self.update_report(parsed_score)
            self.parsed_scores[score_name] = parsed_score


    def extract_samples(self):
        spreadsheet_name = self.spreadsheet_names['Sample']
        current_schema = self.table_mapschema.loc[spreadsheet_name].set_index('Column')

        # Extract data for training (GWAS + Score Development) sample
        for sample_id, sample_info in self.table_samples_scores.iterrows():
            samples_list = []
            sample_data = self.get_sample_data(sample_info,current_schema,spreadsheet_name)

            # Parse from GWAS Catalog
            sample_keys = sample_data.data.keys()
            if 'sample_number' not in sample_keys:
                if 'source_GWAS_catalog' in sample_keys:
                    gwas_study = get_gwas_study(sample_data.data['source_GWAS_catalog'])
                    if gwas_study:
                        for gwas_ancestry in gwas_study:
                            c_sample = SampleData(spreadsheet_name)
                            for col, entry in sample_data.data.items():
                                c_sample.add_data(col, entry)
                            for field, val in gwas_ancestry.items():
                                c_sample.add_data(field, val)
                            self.update_report(c_sample)
                            samples_list.append(c_sample)
                    else:
                        self.report_error(spreadsheet_name, f'Can\'t fetch the GWAS information for the study {sample_data.data["source_GWAS_catalog"]}')
                else:
                    self.report_error(spreadsheet_name, f'Missing GWAS Study ID (GCST ID) to fetch the sample information')
            if len(samples_list) == 0:
                samples_list.append(sample_data)
            self.parsed_samples_scores.append((sample_id, samples_list))

        # Extract data Testing samples
        for testset_name, testsets in self.table_samples_testing.groupby(level=0):
            results = []
            for sample_id, sample_info in testsets.iterrows():
                sample_data = self.get_sample_data(sample_info,current_schema,spreadsheet_name,testset_name)
                results.append(sample_data)
            self.parsed_samples_testing.append((testset_name, results))


    def extract_performances(self):
        ''' Extract the performance and metric data. '''
        spreadsheet_name = self.spreadsheet_names['Performance']
        current_schema = self.table_mapschema.loc[spreadsheet_name].set_index('Column')
        for p_key, performance_info in self.table_performances.iterrows():
            parsed_performance = PerformanceData(spreadsheet_name)
            for col, val in performance_info.items():
                if pd.isnull(val) == False:
                    m, f = self.get_model_field_from_schema(col,current_schema)

                    if m is not None:
                        if f.startswith('metric'):
                            try:
                                parsed_performance.add_metric(f, val)
                            except:
                                if ';' in str(val):
                                    for x in val.split(';'):
                                        parsed_performance.add_metric(f, x)
                                else:
                                    self.report_error(spreadsheet_name, f'Error parsing: {f} {val}')
                        else:
                            parsed_performance.add_data(f, val)

            self.update_report(parsed_performance)
            self.parsed_performances.append((p_key,parsed_performance))


    def get_sample_data(self, sample_info, current_schema, spreadsheet_name, sampleset_name=None):
        ''' Extract the sample data (gwas and dev/training). '''
        sample_data = SampleData(spreadsheet_name,sampleset_name)
        for c, val in sample_info.to_dict().items():
            if c in current_schema.index:
                if pd.isnull(val) == False:
                    f = current_schema.loc[c, 'Field']
                    if pd.isnull(f) == False:
                        if f == 'cohorts':
                            cohorts_list = []
                            for cohort in val.split(','):
                                cohort = cohort.strip()
                                cohort_id = cohort.upper()
                                if cohort_id in self.parsed_cohorts:
                                    cohorts_list.append(self.parsed_cohorts[cohort_id])
                                else:
                                    self.report_error(spreadsheet_name, f'Error: the sample cohort "{cohort}" cannot be found in the Cohort Refr. spreadsheet')
                            val = cohorts_list
                        elif f in ['sample_age', 'followup_time']:
                            val = sample_data.str2demographic(f, val)
                            self.update_report(val)
                        elif f == 'source_PMID':
                            # PubMed ID
                            if isinstance(val, int) or isinstance(val, float):
                                val = int(val) # Convert from float to int
                            # DOI
                            else:
                                f = 'source_DOI'
                                val = str(val)
                        sample_data.add_data(f,val)
        self.update_report(sample_data)
        return sample_data


    def get_model_field_from_schema(self, col, current_schema):
        '''
        Retrieve the model and field from the Template, that corresponds to the current spreadsheet column.
        e.g. "Score Name/ID" -> model: Score |  field: name
        - col: the current column selected
        - current_schema: the template, indexed by the "Column"
        Return types: Django model, string
        '''
        model = None
        field = None
        if col[1] in current_schema.index:
            model, field = current_schema.loc[col[1]][:2]
        elif col[0] in current_schema.index:
             model, field  = current_schema.loc[col[0]][:2]
        return model, field


    #=================================#
    #  Error/warning reports methods  #
    #=================================#

    def add_report(self, type, spreadsheet_name, msg):
        """
        Store the reported error/warning.
        - type: type of report (e.g. error, warning)
        - spreadsheet_name: name of the spreadsheet (e.g. Publication Information)
        - msg: error message
        """
        if type in ['error', 'warning', 'import']:
            if not spreadsheet_name in self.report[type]:
                self.report[type][spreadsheet_name] = set()
            self.report[type][spreadsheet_name].add(msg)
        else:
            print(f'ERROR: Can\'t find the report category "{type}"!')

    def report_error(self, spreadsheet_name, msg):
        """
        Store the reported error.
        - spreadsheet_name: name of the spreadsheet (e.g. Publication Information)
        - msg: error message
        """
        self.add_report('error', spreadsheet_name, msg)

    def report_warning(self, spreadsheet_name, msg):
        """
        Store the reported warning.
        - spreadsheet_name: name of the spreadsheet (e.g. Publication Information)
        - msg: warning message
        """
        self.add_report('warning', spreadsheet_name, msg)

    def update_report(self, obj):
        for type, reports in obj.report.items():
            for sp_name, messages in obj.report[type].items():
                for message in list(messages):
                    self.add_report(type, sp_name, message)

    def display_reports(self):
        """ Return the content of the reports """
        report_msg = []
        for type, reports in self.report.items():
            if reports:
                report_msg.append(f"\n## {type} ##")
                for sp_name, messages in self.report[type].items():
                    for message in list(messages):
                        report_msg.append(f"  - {sp_name}: {message}")
        return '\n'.join(report_msg)


    def has_report_info(self):
        for rtype in self.report.keys():
            if self.report[rtype]:
                return True
        return False


#=======================#
#  Independent methods  #
#=======================#

def get_gwas_study(gcst_id):
    """
    Get the GWAS Study information related to the PGS sample.
    Check that all the required data is available
    > Parameter:
        - gcst_id: GWAS Study ID (e.g. GCST010127)
    > Return: list of dictionnaries (1 per ancestry)
    """
    study_data = []
    gwas_rest_url = 'https://www.ebi.ac.uk/gwas/rest/api/studies/'
    response = requests.get(f'{gwas_rest_url}{gcst_id}')

    if not response:
        return study_data
    response_data = response.json()
    if response_data:
        try:
            source_PMID = response_data['publicationInfo']['pubmedId']
            for ancestry in response_data['ancestries']:

                if ancestry['type'] != 'initial':
                    continue

                ancestry_data = { 'source_PMID': source_PMID }
                ancestry_data['sample_number'] = ancestry['numberOfIndividuals']

                # ancestry_broad
                for ancestralGroup in ancestry['ancestralGroups']:
                    if not 'ancestry_broad' in ancestry_data:
                        ancestry_data['ancestry_broad'] = ''
                    else:
                        ancestry_data['ancestry_broad'] += ','
                    ancestry_data['ancestry_broad'] += ancestralGroup['ancestralGroup']

                # ancestry_free
                for countryOfOrigin in ancestry['countryOfOrigin']:
                    if countryOfOrigin['countryName'] != 'NR':
                        if not 'ancestry_free' in ancestry_data:
                            ancestry_data['ancestry_free'] = ''
                        else:
                            ancestry_data['ancestry_free'] += ','
                        ancestry_data['ancestry_free'] += countryOfOrigin['countryName']

                # ancestry_country
                for countryOfRecruitment in ancestry['countryOfRecruitment']:
                    if countryOfRecruitment['countryName'] != 'NR':
                        if not 'ancestry_country' in ancestry_data:
                            ancestry_data['ancestry_country'] = ''
                        else:
                            ancestry_data['ancestry_country'] += ','
                        ancestry_data['ancestry_country'] += countryOfRecruitment['countryName']
                # ancestry_additional
                # Not found in the REST API

                study_data.append(ancestry_data)
        except:
            print(f'Error: can\'t fetch GWAS results for {gcst_id}')
    return study_data


def next_PSS_num():
    r = SampleSet.objects.last()
    if r == None:
        return 1
    else:
        return r.num + 1
