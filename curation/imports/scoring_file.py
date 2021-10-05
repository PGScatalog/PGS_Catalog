import gzip
import pandas as pd
import numpy as np
import re
from catalog.models import Score


class ScoringFileUpdate():
    ''' Updating the Scoring file by adding a header and gzip it. '''

    def __init__(self, score, study_path, new_scoring_dir, score_file_schema):
        self.score = score
        self.score_file_path = f'{study_path}/raw_scores'
        self.new_score_file_path = new_scoring_dir
        self.score_file_schema = score_file_schema


    def create_scoringfileheader(self):
        '''Function to extract score & publication information for the PGS Catalog Scoring File commented header'''
        score = self.score
        pub = score.publication
        lines = []
        try:
            traits = score.trait_efo
            efo_ids = ','.join([x.id for x in traits])
            mapped_traits = ','.join([x.label for x in traits])
            lines = [
                '### PGS CATALOG SCORING FILE - see https://www.pgscatalog.org/downloads/#dl_ftp_scoring for additional information',
                '## POLYGENIC SCORE (PGS) INFORMATION',
                f'# PGS ID = {score.id}',
                f'# PGS Name = {score.name}',
                f'# Reported Trait = {score.trait_reported}',
                f'# EFO ID(s) = {efo_ids}',
                f'# Mapped Trait(s) (EFO) = {mapped_traits}',
                f'# Original Genome Build = {score.variants_genomebuild}',
                f'# Number of Variants = {score.variants_number}',
                '## SOURCE INFORMATION',
                f'# PGP ID = {pub.id}'
            ]
            if pub.firstauthor and pub.journal and pub.pub_year and pub.doi:
                lines.append(f'# Citation = {pub.firstauthor} et al. {pub.journal} ({pub.pub_year}). doi:{pub.doi}')

            if score.license != Score._meta.get_field('license')._get_default():
                ltext = score.license.replace('\n', ' ')     # Make sure there are no new-lines that would screw up the commenting
                lines.append('# LICENSE = {}'.format(ltext)) # Append to header
        except Exception as e:
            print(f'Header creation issue: {e}')
        return lines


    def update_scoring_file(self):
        ''' Method to fetch the file, read it, add the header and compress it. '''
        failed_update = False
        try:
            score_name = self.score.name
            score_id = self.score.id
            raw_scorefile = f'{self.score_file_path}/{score_name}.txt'
            df_scoring = pd.read_table(raw_scorefile, dtype='str', engine = 'python')

            # Check that all columns are in the schema
            column_check = True
            for x in df_scoring.columns:
                if not x in self.score_file_schema.index:
                    column_check = False
                    print(f'The column "{x}" is not in the Schema index')
                    break

            if column_check == True:
                # Get new header
                header = self.create_scoringfileheader()
                if len(header) == 0:
                    failed_update = True
                    return failed_update

                # Check if weight_type in columns
                if 'weight_type' in df_scoring.columns:
                    if all(df_scoring['weight_type']):
                        val = df_scoring['weight_type'][0]
                        if val == 'OR':
                            df_scoring = df_scoring.rename({'effect_weight' : 'OR'}, axis='columns').drop(['weight_type'], axis=1)
                if 'effect_weight' not in df_scoring.columns:
                    if 'OR' in df_scoring.columns:
                        df_scoring['effect_weight'] = np.log(pd.to_numeric(df_scoring['OR']))
                        df_scoring['weight_type'] = 'log(OR)'
                    elif 'HR' in df_scoring.columns:
                        df_scoring['effect_weight'] = np.log(pd.to_numeric(df_scoring['HR']))
                        df_scoring['weight_type'] = 'log(HR)'

                # Reorganize columns according to schema
                corder = []
                for x in self.score_file_schema.index:
                    if x in df_scoring.columns:
                        corder.append(x)

                df_scoring = df_scoring[corder]
                df_csv = df_scoring.to_csv(sep='\t', index=False)
                # Cleanup the file by removing empty lines
                new_df_csv = []
                for row in df_csv.split('\n'):
                    if not re.match('^\t*$', row):
                        new_df_csv.append(row)
                df_csv = '\n'.join(new_df_csv)

                with gzip.open(f'{self.new_score_file_path}/{score_id}.txt.gz', 'w') as outf:
                    outf.write('\n'.join(header).encode('utf-8'))
                    outf.write('\n'.encode('utf-8'))
                    outf.write(df_csv.encode('utf-8'))
            else:
                badmaps = []
                for i, v in enumerate(column_check):
                    if v == False:
                        badmaps.append(df_scoring.columns[i])
                failed_update = True
                print(f'ERROR in {raw_scorefile} ! bad columns: {badmaps}')
        except Exception as e:
            failed_update = True
            print(f'ERROR reading scorefile: {raw_scorefile}\n-> {e}')
        return failed_update
