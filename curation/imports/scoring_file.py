import os, re, gzip
import pandas as pd
import numpy as np
from catalog.models import Score
from curation.scripts.qc_ref_genome import sample_df, map_rsids, map_variants_to_reference_genome, usecols


class ScoringFileUpdate():
    ''' Updating the Scoring file by adding a header and gzip it. '''

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

    def create_scoringfileheader(self):
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
            print(f'Header creation issue: {e}')
        return lines

    def update_scoring_file(self):
        ''' Method to fetch the file, read it, add the header and compress it. '''
        failed_update = False
        score_id = self.score.id
        score_name = self.score.name
        raw_scorefile_path = f'{self.score_file_path}/{score_name}'
        try:
            raw_scorefile_txt = f'{raw_scorefile_path}{self.txt_ext}'
            raw_scorefile_tsv = f'{raw_scorefile_path}{self.tsv_ext}'
            raw_scorefile_xls = f'{raw_scorefile_path}{self.xls_ext}'
            if os.path.exists(raw_scorefile_txt):
                df_scoring = pd.read_table(raw_scorefile_txt, dtype='str', engine='python')
            elif os.path.exists(raw_scorefile_tsv):
                df_scoring = pd.read_table(raw_scorefile_tsv, dtype='str', engine='python')
            elif os.path.exists(raw_scorefile_xls):
                df_scoring = pd.read_excel(raw_scorefile_xls, dtype='str')
            else:
                failed_update = True
                print(f"ERROR can't find the scorefile {raw_scorefile_path} (trying with the extensions '{self.txt_ext}' and '{self.xls_ext}')\n")
                return failed_update

            # Remove empty columns
            df_scoring.replace("", float("NaN"), inplace=True)
            df_scoring.dropna(how='all', axis=1, inplace=True)

            # Rename reference_allele column
            if 'other_allele' not in df_scoring.columns and 'reference_allele' in df_scoring.columns:
                df_scoring.rename(columns={'reference_allele': 'other_allele'}, inplace=True)

            # Check that all columns are in the schema
            column_check = True
            for x in df_scoring.columns:
                if not x in self.score_file_schema.index and x != self.weight_type_label:
                    # Skip custom allele frequency effect columns
                    if not x.startswith('allelefrequency_effect_'):
                        column_check = False
                        print(f'The column "{x}" is not in the Schema index')
                        break

            if column_check == True:
                # Check if weight_type in columns
                weight_type_value = None
                if self.weight_type_label in df_scoring.columns:
                    if all(df_scoring[self.weight_type_label]):
                        val = df_scoring[self.weight_type_label][0]
                        weight_type_value = val
                        if val == 'OR':
                            df_scoring = df_scoring.rename({'effect_weight' : 'OR'}, axis='columns').drop([self.weight_type_label], axis=1)
                if 'effect_weight' not in df_scoring.columns:
                    if 'OR' in df_scoring.columns:
                        df_scoring['effect_weight'] = np.log(pd.to_numeric(df_scoring['OR']))
                        weight_type_value = 'log(OR)'
                    elif 'HR' in df_scoring.columns:
                        df_scoring['effect_weight'] = np.log(pd.to_numeric(df_scoring['HR']))
                        weight_type_value = 'log(HR)'

                # Update Score model with weight_type data
                if weight_type_value:
                    self.score.weight_type = weight_type_value
                    self.score.save()

                # Get new header
                header = self.create_scoringfileheader()
                if len(header) == 0:
                    failed_update = True
                    return failed_update

                # Reorganize columns according to schema
                col_order = []
                for x in self.score_file_schema.index:
                    if x in df_scoring.columns:
                        col_order.append(x)

                df_scoring = df_scoring[col_order]
                df_csv = df_scoring.to_csv(sep='\t', index=False)
                # Cleanup the file by removing empty lines
                new_df_csv = []
                for row in df_csv.split('\n'):
                    if not re.match('^\t*$', row):
                        new_df_csv.append(row)
                df_csv = '\n'.join(new_df_csv)

                new_score_file = f'{self.new_score_file_path}/{score_id}.txt.gz'
                with gzip.open(new_score_file, 'w') as outf:
                    outf.write('\n'.join(header).encode('utf-8'))
                    outf.write('\n'.encode('utf-8'))
                    outf.write(df_csv.encode('utf-8'))
            else:
                badmaps = []
                for i, v in enumerate(column_check):
                    if v == False:
                        badmaps.append(df_scoring.columns[i])
                failed_update = True
                print(f'ERROR in {raw_scorefile_path} ! bad columns: {badmaps}')
        except Exception as e:
            failed_update = True
            print(f'ERROR reading scorefile: {raw_scorefile_path}\n-> {e}')
        return failed_update


class VariantPositionsQC:

    def __init__(self, score, new_scoring_dir, variant_positions_qc_config):
        self.score = score
        self.new_score_file_path = new_scoring_dir
        self.variant_positions_qc_config = variant_positions_qc_config

    def qc_variant_positions(self, report_func=print, error_func=print) -> bool:
        """ QC the variant positions regarding the assigned genome build of the scoring file."""
        failed_qc = False
        score = self.score
        genome_build = score.variants_genomebuild
        if not genome_build:
            failed_qc = True
            error_func(f'Missing genome build')
        build_version = None
        if genome_build in ('GRCh37', 'hg19'):
            build_version = '37'
        elif genome_build in ('GRCh38', 'hg38'):
            build_version = '38'
        elif genome_build == 'NR':
            report_func('Genome build = NR, variant positions validation ignored.')
            return failed_qc
        else:
            report_func(f'Genome build = "{genome_build}", not detected as 37 or 38, variant positions validation ignored.')
            return failed_qc
        report_func(f'Build version = {build_version}')

        new_score_file = f'{self.new_score_file_path}/{score.id}.txt.gz'

        # Reading the scoring file
        df = pd.read_csv(new_score_file,
                         sep="\t",
                         comment='#',
                         usecols=lambda c: c in usecols,
                         dtype={"rsID": 'string', "chr_name": 'string', "chr_position": 'Int64',
                                "effect_allele": 'string', "other_allele": 'string'})

        if 'chr_position' not in df.columns:
            report_func('No chr_position column. Variant position QC will be skipped')
            return failed_qc

        # Headers for alleles. other_allele is optional, but should be tested if exists as we don't know which allele is the reference one.
        alleles_headers = ['effect_allele']
        if 'other_allele' in df.columns:
            alleles_headers.append('other_allele')

        n_requests = self.variant_positions_qc_config['n_requests']

        if 'rsID' in df.columns:
            max_request_size = self.variant_positions_qc_config['ensembl_max_variation_req_size']
            map_variants_func = map_rsids
        else:
            if len(alleles_headers) == 1:
                # 1 allele column is not enough for sequence-based validation, as we don't know if the allele is ref or alt.
                report_func('Only 1 allele column with no rsID. Variant position QC will be skipped')
                return failed_qc
            max_request_size = self.variant_positions_qc_config['ensembl_max_sequence_req_size']
            map_variants_func = map_variants_to_reference_genome

        errors = []
        variant_slices = sample_df(df, n_requests, max_request_size, alleles_headers, False, errors)

        match = 0
        mismatch = 0
        for variants in variant_slices:
            results = map_variants_func(variants, build_version)
            match += results['match']
            mismatch += results['mismatch']
            errors = errors + results['errors']

        final_report = '''Results:
         - Matches: {0}
         - Mismatches: {1}'''
        report_func(final_report.format(str(match), str(mismatch)))

        minimum_match_rate = self.variant_positions_qc_config['minimum_match_rate']

        # Fail if low match rate
        if match+mismatch == 0:
            report_func('WARNING: No match data!')
        else:
            match_rate: float = float(match) / (match + mismatch)
            report_func(f'Match rate: {match_rate}')
            if match_rate < minimum_match_rate:
                error_func('Low match rate! The assigned genome build might be incorrect')
                failed_qc = True

        return failed_qc
