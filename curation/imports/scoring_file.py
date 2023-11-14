import os, re, gzip, random
import pandas as pd
import numpy as np
import requests
from catalog.models import Score


class ScoringFileUpdate():
    ''' Updating the Scoring file by adding a header and gzip it. '''

    gb_map = {
        'hg19': 'GRCh37',
        'hg38': 'GRCh38',
        'GRCh37': 'GRCh37',
        'GRCh38': 'GRCh38'
    }
    nb_rows_to_test = 10

    value_separator = '|'
    weight_type_label = 'weight_type'
    txt_ext = '.txt'
    tsv_ext = '.tsv'
    xls_ext = '.xlsx'

    def __init__(self, score, study_path, new_scoring_dir, score_file_schema, score_file_format_version):
        self.score = score
        self.new_score_file_path = new_scoring_dir
        self.score_file_schema = score_file_schema
        self.score_file_format_version = score_file_format_version
        self.score_file_path = f'{study_path}/raw_scores'
        if not os.path.isdir(self.score_file_path):
            self.score_file_path = f'{study_path}/raw scores'


    def create_scoringfileheader(self) -> list:
        '''Function to extract score & publication information for the PGS Catalog Scoring File commented header'''
        score = self.score
        pub = score.publication
        lines = []
        try:
            traits = score.trait_efo.all()
            efo_ids = self.value_separator.join([x.id for x in traits])
            mapped_traits = self.value_separator.join([x.label for x in traits])
            lines = [
                '###PGS CATALOG SCORING FILE - see https://www.pgscatalog.org/downloads/#dl_ftp_scoring for additional information',
                f'#format_version={self.score_file_format_version}',
                '##POLYGENIC SCORE (PGS) INFORMATION',
                f'#pgs_id={score.id}',
                f'#pgs_name={score.name}',
                f'#trait_reported={score.trait_reported}',
                f'#trait_mapped={mapped_traits}',
                f'#trait_efo={efo_ids}',
                f'#genome_build={score.variants_genomebuild}',
                f'#variants_number={score.variants_number}',
                f'#weight_type={score.weight_type}',
                '##SOURCE INFORMATION',
                f'#pgp_id={pub.id}'
            ]
            if pub.firstauthor and pub.journal and pub.pub_year and pub.doi:
                lines.append(f'#citation={pub.firstauthor} et al. {pub.journal} ({pub.pub_year}). doi:{pub.doi}')

            if score.license != Score._meta.get_field('license')._get_default():
                ltext = score.license.replace('\n', ' ')     # Make sure there are no new-lines that would screw up the commenting
                lines.append('#license={}'.format(ltext)) # Append to header
        except Exception as e:
            self.print_report(f'Header creation issue: {e}')
        return lines


    def check_rsID_gb_coords(self, genome_build:str) -> bool:
        ''' Compare variants coordinates between the scoring file and Ensembl, using the given genome build. '''
        failed_gb_check = False
        rsids_list = []
        var_coords = {}
        sample_data_frame = self.generate_check_rsID_sample()
        if len(sample_data_frame) == 0:
            self.print_report(f"ERROR with Genome build check: the sample dataframe is empty!")
            failed_gb_check == True
        else:
            for index, row in sample_data_frame.iterrows():
                rsid = row['rsID']
                rsids_list.append(rsid)
                var_coords[rsid] = {
                    'chr': row['chr_name'],
                    'start': row['chr_position']
                }
            ens_vars = self.rest_ensembl_post(rsids_list, genome_build)
            if len(ens_vars.keys()):
                count_match = 0
                count_var = 0
                # Count coordinates match
                for var_id in rsids_list:
                    var_score_mapping = var_coords[var_id]
                    if var_id in ens_vars.keys():
                        count_var += 1
                        for mapping in ens_vars[var_id]:
                            if str(mapping['chr']) == str(var_score_mapping['chr']) and str(mapping['start']) == str(var_score_mapping['start']):
                                count_match += 1
                                break
                # Report of the checks
                if count_var < len(rsids_list):
                    failed_gb_check = True
                    self.print_report(f"ERROR with Genome build check: {count_var}/{len(rsids_list)} of the test variants have been retrieved via Ensembl.")
                elif count_match != count_var and count_var != 0:
                    failed_gb_check = True
                    self.print_report(f"ERROR with Genome build check: {count_match}/{count_var} of the test variants coordinates match Ensembl's variant coordinates on '{genome_build}'.")
                if failed_gb_check == True:
                    self.print_report(f"Variants tested: {','.join(rsids_list)}", True)
        return failed_gb_check


    def generate_check_rsID_sample(self) -> pd.DataFrame:
        """Method to generate a randomised sample dataframe from the main dataframe in order to check the genome assembly"""
        index_length = len(self.df_scoring)
        row_index_list = []
        rsid_regex = '^rs\d+$'
        # Get list of dataframe indexes to use in the sample dataframe
        if self.nb_rows_to_test > index_length:
            self.nb_rows_to_test = index_length
            row_index_list = list(df.index.values)
        else:
            row_index_list = sorted(random.sample(range(0, index_length-1), self.nb_rows_to_test))
        # Initial sample dataframe
        df_sample = self.df_scoring.iloc[row_index_list]
        rebuild_df_sample_flag = False
        legacy_row_index_list = set(row_index_list)
        new_row_index_list = []
        # Check if each row contains a well formatted rsID (i.e. rs[0-9]+)
        for index, row in df_sample.iterrows():
            rsid = row['rsID']
            if re.search(rsid_regex,str(rsid)):
                new_row_index_list.append(index)
            else:
                rebuild_df_sample_flag = True
                new_index = index
                new_index_found = None
                count = 0
                # Find replacement rows in the original dataframe (i.e. with a well formatted rsID)
                while new_index_found == None and count<(index_length-len(legacy_row_index_list)):
                    new_index = random.randint(0, index_length-1)
                    count += 1
                    # Check if the new row index has been already seen
                    if new_index not in legacy_row_index_list:
                        # Check if the rsID from the new row is well formatted
                        if re.search(rsid_regex,str(self.df_scoring.iloc[new_index]['rsID'])):
                            # Add row index to the new list
                            new_row_index_list.append(new_index)
                            legacy_row_index_list.add(new_index)
                            new_index_found = new_index
        # Regenerate the sample dataframe with entries having a well formatted rsID
        if rebuild_df_sample_flag:
            df_sample = self.df_scoring.iloc[sorted(new_row_index_list)]
            # Reset the number of rsID to test, depending on the size of the sample dataframe
            self.nb_rows_to_test = len(df_sample)
        return df_sample


    def update_scoring_file(self) -> bool:
        ''' Method to fetch the file, read it, add the header and compress it. '''
        failed_update = False
        score_id = self.score.id
        score_name = self.score.name
        raw_scorefile_path = f'{self.score_file_path}/{score_name}'
        print(f"\n# {score_name}:")
        try:
            raw_scorefile_txt = f'{raw_scorefile_path}{self.txt_ext}'
            raw_scorefile_tsv = f'{raw_scorefile_path}{self.tsv_ext}'
            raw_scorefile_xls = f'{raw_scorefile_path}{self.xls_ext}'
            if os.path.exists(raw_scorefile_txt):
                self.df_scoring = pd.read_table(raw_scorefile_txt, dtype='str', engine = 'python')
            elif os.path.exists(raw_scorefile_tsv):
                self.df_scoring = pd.read_table(raw_scorefile_tsv, dtype='str', engine = 'python')
            elif os.path.exists(raw_scorefile_xls):
                self.df_scoring = pd.read_excel(raw_scorefile_xls, dtype='str', engine = 'python')
            else:
                failed_update = True
                self.print_report(f"ERROR can't find the scorefile {raw_scorefile_path} (trying with the extensions '{self.txt_ext}' and '{self.xls_ext}')", True)
                return failed_update

            # Remove empty columns
            self.df_scoring.replace("", float("NaN"), inplace=True)
            self.df_scoring.dropna(how='all', axis=1, inplace=True)

            # Rename reference_allele column
            if 'other_allele' not in self.df_scoring.columns and 'reference_allele' in self.df_scoring.columns:
                self.df_scoring.rename(columns={'reference_allele': 'other_allele'}, inplace=True)


            if self.check_columns():

                print(f"  - Check that the coordinates of the variants matches the ones on the given genome build")
                # Check the genome build of the variants to make sure they match the given genome build of the score
                gb = self.score.variants_genomebuild
                # Check genome build
                if gb in self.gb_map.keys() and 'rsID' in self.df_scoring.columns:
                    # df_sample = self.df_scoring.head(self.nb_rows_to_test)
                    # failed_update = self.check_rsID_gb_coords(self.gb_map[gb],df_sample)
                    failed_update = self.check_rsID_gb_coords(self.gb_map[gb])
                    if failed_update == False:
                        self.print_report('Genome build matches the variants coordinates')
                else:
                    if gb not in self.gb_map.keys():
                        self.print_report(f"Skip the check the coordinates of the variants for {score_name}: the genome assembly '{gb}' can't be checked")
                    if 'rsID' not in self.df_scoring.columns:
                        self.print_report(f"Skip the check the coordinates of the variants for {score_name}: no 'rsID' column found in this scoring file")
                if failed_update == True:
                    self.print_report(f"ERROR: the genome build of the variant coordinates doesn't match the genome build of the score")
                    return failed_update

                print(f"  - Update/cleanup columns")
                # Check if weight_type in columns
                self.update_weight_type()

                # Get new header
                header = self.create_scoringfileheader()
                if len(header) == 0:
                    failed_update = True
                    return failed_update

                # Reorganize columns according to schema
                col_order = []
                for x in self.score_file_schema.index:
                    if x in self.df_scoring.columns:
                        col_order.append(x)

                self.df_scoring = self.df_scoring[col_order]
                df_csv = self.df_scoring.to_csv(sep='\t', index=False)
                # Cleanup the file by removing empty lines
                new_df_csv = []
                for row in df_csv.split('\n'):
                    if not re.match('^\t*$', row):
                        new_df_csv.append(row)
                df_csv = '\n'.join(new_df_csv)

                print(f"  - Add metadata headers")
                updated_scoring_file_path = f'{self.new_score_file_path}/{score_id}.txt.gz'
                with gzip.open(updated_scoring_file_path, 'w') as outf:
                    outf.write('\n'.join(header).encode('utf-8'))
                    outf.write('\n'.encode('utf-8'))
                    outf.write(df_csv.encode('utf-8'))
                if os.path.isfile(updated_scoring_file_path):
                    if os.stat(updated_scoring_file_path).st_size != 0:
                        print(f"  >> Updated Scoring File has been generated in {updated_scoring_file_path}")
            else:
                badmaps = []
                for i, v in enumerate(column_check):
                    if v == False:
                        badmaps.append(self.df_scoring.columns[i])
                failed_update = True
                self.print_report(f'ERROR in {raw_scorefile_path} ! bad columns: {badmaps}')
        except Exception as e:
            failed_update = True
            self.print_report(f'ERROR reading scorefile: {raw_scorefile_path}\n    -> {e}')
        return failed_update


    def check_columns(self) -> bool:
        """Check that all columns are in the schema"""
        column_check = True
        for x in self.df_scoring.columns:
            if not x in self.score_file_schema.index and x != self.weight_type_label:
                # Skip custom allele frequency effect columns
                if not x.startswith('allelefrequency_effect_'):
                    column_check = False
                    self.print_report(f'The column "{x}" is not in the Schema index')
                    break
        return column_check


    def update_weight_type(self) -> None:
        """Check if weight_type in columns. If so, it tries to update the columns and dataframe"""
        weight_type_value = None
        if self.weight_type_label in self.df_scoring.columns:
            if all(self.df_scoring[self.weight_type_label]):
                val = self.df_scoring[self.weight_type_label][0]
                weight_type_value = val
                if val == 'OR':
                    self.df_scoring = self.df_scoring.rename({'effect_weight' : 'OR'}, axis='columns').drop([self.weight_type_label], axis=1)
        if 'effect_weight' not in self.df_scoring.columns:
            if 'OR' in self.df_scoring.columns:
                self.df_scoring['effect_weight'] = np.log(pd.to_numeric(self.df_scoring['OR']))
                weight_type_value = 'log(OR)'
            elif 'HR' in self.df_scoring.columns:
                self.df_scoring['effect_weight'] = np.log(pd.to_numeric(self.df_scoring['HR']))
                weight_type_value = 'log(HR)'

        # Update Score model with weight_type data
        if weight_type_value:
            self.score.weight_type = weight_type_value
            self.score.save()


    def rest_ensembl_post(self, rsid_list:list, genome_build:str) -> dict:
        """Retrieve rsID info from ENSEMBL Variation API"""

        rest_api = {
            'GRCh37': 'https://grch37.rest.ensembl.org/variation/homo_sapiens',
            'GRCh38': 'https://rest.ensembl.org/variation/homo_sapiens'
        }
        chromosomes_list = ['1','2','3','4','5','6','7','8','9','10','11','12','13','14','15','16','17','18','19','20','21','22','X','Y','MT']

        rest_headers = {"Content-Type": "application/json", "Accept": "application/json"}

        variants_data = {}
        try:
            data_ids = '","'.join(rsid_list)
            response = requests.post(rest_api[genome_build], headers=rest_headers, data='{ "ids":["'+data_ids+'"]}')
            response_json = response.json()
            response_json_ids = response_json.keys()
            variants_found = []
            for id in rsid_list:
                if id in response_json_ids:
                    variants_found.append(id)
                    variant_json = response_json[id]
                    if 'name' in variant_json:
                        mappings = []
                        for location in variant_json['mappings']:
                           chr = str(location['seq_region_name'])
                           if chr in chromosomes_list:
                               start = location['start']
                               mappings.append({'chr':chr, 'start':start})
                        if mappings and len(mappings) > 0:
                            variants_data[id] = mappings
        except requests.exceptions.RequestException as e:  # This is the correct syntax
            self.print_report(f"Error: cant't retrieve the variant information via the Ensembl REST API: {e}")
        return variants_data


    def print_report(self,msg:str,sub:bool=False) -> None:
        if sub:
            print(f'      -> {msg}')
        else:
            print(f'    > {msg}')
