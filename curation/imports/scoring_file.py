import gzip
import os
import re
import shutil
from pathlib import Path
from typing import Iterator

import numpy as np
import pandas as pd

from catalog.models import Score
from curation.scripts.qc_ref_genome import sample_df, map_rsids, map_variants_to_reference_genome, usecols


class ScoringFileUpdate():
    ''' Updating the Scoring file by adding a header and gzip it. '''

    value_separator = '|'
    weight_type_label = 'weight_type'
    extensions = ('txt', 'tsv', 'xlsx')

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

    @classmethod
    def read_csv_in_chunks(cls, file_path, file_format: str) -> Iterator[pd.DataFrame]:
        """ Read the given raw scoring file in chunks to avoid potential OOM error occurring with big files."""
        chunk_size = 2000000  # Around 2GB memory
        match file_format:
            case ('txt' | 'tsv'):
                for chunk in pd.read_table(file_path, dtype='str', engine='python', chunksize=chunk_size):
                    yield chunk
            case ('xls'):
                # Chunk reading not possible with spreadsheets. If too big, it might be preferable to convert them
                # to text files.
                yield pd.read_excel(file_path, dtype='str')
            case _:
                raise ValueError(f'Unsupported file format: {file_format}')

    @classmethod
    def compress_file(cls, file_name):
        """ Compress the input file and append '.gz' extension. """
        file_path = Path(file_name)
        gzipped_path = Path(file_name + '.gz')
        with open(file_path, 'rb') as f_in, gzip.open(gzipped_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
        file_path.unlink()

    @classmethod
    def check_file_exists(cls, file_name: str):
        """Checks if the given file exists. If yes, it is moved to a temporary directory (<output_dir>/trashcan) for review.
        Checks for both uncompressed and compressed versions."""
        for file_path in (Path(file_name), Path(file_name+".gz")):
            if file_path.exists():
                # Move to local trash can folder. Will be overwritten if already in trash can.
                trashcan_folder = file_path.parent / "trashcan"
                trashcan_folder.mkdir(exist_ok=True)
                file_path.replace(trashcan_folder / file_path.name)
                print(f"WARNING: The file {file_path} already exists. It has been moved to {trashcan_folder}")

    def update_scoring_file(self):
        """ Method to fetch the file, read it, add the header and compress it. """
        failed_update = False
        score_id = self.score.id
        score_name = self.score.name
        raw_scorefile_path = f'{self.score_file_path}/{score_name}'
        new_score_file = f'{self.new_score_file_path}/{score_id}.txt'
        self.check_file_exists(new_score_file)
        try:
            for extension in self.extensions:
                file_path = f'{raw_scorefile_path}.{extension}'
                if os.path.exists(file_path):
                    df_chunks = self.read_csv_in_chunks(file_path=file_path, file_format=extension)
                    break
            else:
                failed_update = True
                print(f"ERROR can't find the score file {raw_scorefile_path}.{str(self.extensions)})\n")
                return failed_update

            first_chunk = True
            for df_scoring in df_chunks:
                header = ''  # This is the metadata header, not the column names.
                if first_chunk:
                    # Check that all columns are in the schema
                    invalid_columns = []
                    for x in df_scoring.columns:
                        if all([
                            x not in self.score_file_schema.index,
                            x != self.weight_type_label,
                            not x.startswith('allelefrequency_effect_')
                        ]):
                            invalid_columns.append(x)
                    if invalid_columns:
                        failed_update = True
                        print(f'ERROR in {raw_scorefile_path} ! The column(s) "{str(invalid_columns)}" are not in the Schema index')
                        return failed_update

                    # Check if weight_type in columns
                    weight_type_value = None
                    if self.weight_type_label in df_scoring.columns:
                        if all(df_scoring[self.weight_type_label]):
                            val = df_scoring[self.weight_type_label][0]
                            weight_type_value = val
                            if val == 'OR':
                                df_scoring = df_scoring.rename({'effect_weight': 'OR'}, axis='columns').drop(
                                    [self.weight_type_label], axis=1)
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

                    first_chunk = False

                # Remove empty columns
                df_scoring.replace("", float("NaN"), inplace=True)
                df_scoring.dropna(how='all', axis=1, inplace=True)

                # Rename reference_allele column
                if 'other_allele' not in df_scoring.columns and 'reference_allele' in df_scoring.columns:
                    df_scoring.rename(columns={'reference_allele': 'other_allele'}, inplace=True)

                # Reorganize columns according to schema
                col_order = []
                for x in self.score_file_schema.index:
                    if x in df_scoring.columns:
                        col_order.append(x)

                df_scoring = df_scoring[col_order]
                df_csv = df_scoring.to_csv(sep='\t', index=False, header=bool(header))  # Header (column names) only if first chunk
                # Cleanup the file by removing empty lines
                new_df_csv = []
                for row in df_csv.split('\n'):
                    if not re.match('^\t*$', row):
                        new_df_csv.append(row)
                df_csv = '\n'.join(new_df_csv)

                # Opening the output file in 'append' mode as we print by chunks. The file should not exist
                # already as we check that previously.
                with open(new_score_file, 'a', encoding='utf-8') as output_file:
                    if header:  # Only first chunk
                        output_file.write('\n'.join(header))
                        output_file.write('\n')
                    output_file.write(df_csv)
                    output_file.write('\n')

            # Compressing only at the end as the file is written in chunks.
            self.compress_file(new_score_file)

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
