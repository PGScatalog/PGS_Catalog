import sys
import pandas as pd
import subprocess
import requests
from requests.adapters import HTTPAdapter, Retry
import json
import argparse
import re
from typing import TypedDict

# Ensembl REST server config
servers = {
   '37': 'https://grch37.rest.ensembl.org',
   '38': 'https://rest.ensembl.org/'
}
ext_seq = "/sequence/region/human"
ext_var = "/variation/human"
headers = {"Content-Type": "application/json", "Accept": "application/json"}
MAX_SEQUENCE_REQUEST_SIZE = 50
MAX_VARIATION_REQUEST_SIZE = 10  # maximum is 200, although it causes some requests to return no result

usecols = ("rsID", "chr_name", "chr_position", "effect_allele", "other_allele")


class Variant(TypedDict):
    rsID: str
    chr: str
    pos: int
    alleles: list[str]


class MappingResults(TypedDict):
    match: int
    mismatch: int
    errors: list[str]


def report(msg: str, submsgs=None):
    if submsgs is None:
        submsgs = []
    print('# ' + msg)
    for submsg in submsgs:
        print('#    - ' + submsg)


def warn(msg: str):
    sys.stderr.write(msg + "\n")


compl_alleles = {'A': 'T', 'T': 'A', 'G': 'C', 'C': 'G'}


def flip_alleles(alleles: list[str]):
    """Flip the given alleles for checking for the reverse strand"""
    return [reverse_complement(a) for a in alleles]


def reverse_complement(seq: str):
    return ''.join(compl_alleles[n] for n in reversed(seq.upper()))


def post_request_with_retry(url, data, retry: int = 0):
    """Send a POST request to the given URL. The request will be retried up to specified number of times
    if the returned response is empty yet successful (happens with Ensembl Variation API)"""
    s = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504],
                    allowed_methods=frozenset(['GET', 'POST']))
    s.mount('http://', HTTPAdapter(max_retries=retries))
    s.mount('https://', HTTPAdapter(max_retries=retries))
    r = s.post(url, headers=headers, data=json.dumps(data))

    if not r.ok:
        r.raise_for_status()
        quit()

    result = r.json()
    if retry and not result:  # Sometimes Ensembl returns an empty response (although status 200)
        warn('Returned empty results. Retrying request (remaining attempts: %i)' % retry)
        result = post_request_with_retry(url, data, retry - 1)

    return result


def get_variation_from_ensembl(rsids: list[str], ref_genome):
    url = servers[ref_genome] + ext_var
    data = {'ids': rsids}
    return post_request_with_retry(url, data, 4)


def get_ref_alleles_from_ensembl(variants: list[Variant], ref_genome):
    url = servers[ref_genome] + ext_seq
    data = {"regions": ["{}:{}-{}".format(v['chr'], v['pos'], v['pos']+max_variant_length(v)-1) for v in variants]}
    return post_request_with_retry(url, data)


def max_variant_length(variant: Variant):
    return max(len(allele) for allele in variant['alleles'])


def map_variants_to_reference_genome(variants: list[Variant], ref_genome) -> MappingResults:
    """Maps the given variants to their reference genome using their coordinates and the Ensembl Sequence API."""
    if len(variants) == 0:
        return {'match': 0, 'mismatch': 0, 'errors': []}
    response = get_ref_alleles_from_ensembl(variants, ref_genome)
    match = 0
    mismatch = 0
    errors = []
    variants_dict = {"{}:{}-{}".format(v['chr'], v['pos'], v['pos']+max_variant_length(v)-1): v['alleles'] for v in variants}
    for resp in response:
        try:
            seq = resp['seq']
            query = resp['query']
            if match_seq_to_variant(seq, variants_dict[query]):
                match += 1
            else:
                mismatch += 1
        except Exception as e:
            errors.append(str(e))

    return {'match': match, 'mismatch': mismatch, 'errors': errors}


def match_seq_to_variant(seq: str, alleles: list[str]) -> bool:
    return True in [seq.upper().startswith(a.upper()) for a in alleles]


def map_rsids(variants: list[Variant], ref_genome) -> MappingResults:
    """Maps the given variants to their reference genome using their rsIDs and the Ensembl Variation API."""
    if len(variants) == 0:
        return {'match': 0, 'mismatch': 0, 'errors': []}
    response = get_variation_from_ensembl([v['rsID'] for v in variants], ref_genome)
    match = 0
    mismatch = 0
    errors = []
    for variant in variants:
        try:
            mapping = response[variant['rsID']]['mappings'][0]
            position = mapping['start']
            if position == variant['pos']:
                match += 1
            else:
                mismatch += 1
        except Exception as e:
            errors.append(str(e))
    return {'match': match, 'mismatch': mismatch, 'errors': errors}


def get_alleles(row, alleles_headers: list[str]):
    """Gets the alleles of the given row and checks that they are valid."""
    alleles = []
    for colname in alleles_headers:
        allele = row[colname]
        if not bool(re.match('^[ATCG]+$', allele.upper())):
            raise Exception("Unexpected allele '{}'.".format(allele))
        alleles.append(allele)
    return alleles


def sample_df(scoring_file_df, n_requests, max_request_size, alleles_headers, flip, errors) -> list[list[Variant]]:
    """Gets n random variant samples of the given size from the given scoring file pandas dataframe."""
    variants_slices = []
    df = scoring_file_df
    for i in range(n_requests):
        variants = []
        # Sampling up to <max_request_size> variants from the scoring file
        sample_size = min(max_request_size, len(df.index))
        if sample_size == 0:
            break
        sample = df.sample(n=sample_size)
        df = df.drop(sample.index)  # Removing the sampled variants from the whole batch
        for index, row in sample.iterrows():
            try:
                chr_name = row['chr_name']
                chr_position = row['chr_position']
                if pd.isna(chr_position):
                    errors.append(f'Position[{index}] is NA')
                    continue

                alleles = get_alleles(row, alleles_headers)
                if flip:
                    alleles = flip_alleles(alleles)
                variant = {"chr": chr_name, "pos": chr_position, "alleles": alleles}
                if 'rsID' in df.columns:
                    variant['rsID'] = row['rsID']
                variants.append(variant)
            except Exception as e:
                errors.append(str(e))

        variants_slices.append(variants)
    return variants_slices


def main():
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("--scoring_file", help="An unzipped scoring file")
    parser.add_argument("--ref", choices=["auto", "37", "38"], default="auto",
                        help="Reference genome. Allowed values: auto,37,38. If auto, the scoring file header genome_build attribute will be used.")
    parser.add_argument("--n_requests", type=int, default=1,
                        help="Number of requests of size 50 (maximum allowed per Ensembl POST request). Default: 1")
    parser.add_argument("--flip", default=False, action=argparse.BooleanOptionalAction)
    parser.add_argument("--use_pos", default=False, action=argparse.BooleanOptionalAction)

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    scoring_file = args.scoring_file
    n_requests = args.n_requests

    # Getting the reference genome from the scoring file if not defined
    ref_genome = None
    if args.ref == 'auto':
        grep_output = subprocess.run(['grep', '-m 1', 'genome_build', scoring_file], stdout=subprocess.PIPE).stdout.decode('utf-8').split("\n")[0]
        ref_genome = re.sub("[^0-9]", "", grep_output.split('=')[1])
        if ref_genome == "19":
            ref_genome = "37"
    else:
        ref_genome = args.ref

    flip = args.flip
    use_pos = args.use_pos

    # Reading the scoring file
    df = pd.read_csv(scoring_file,
                     sep="\t",
                     comment='#',
                     usecols=lambda c: c in usecols,
                     dtype={"rsID": 'string', "chr_name": 'string', "chr_position": 'Int64', "effect_allele": 'string',
                            "other_allele": 'string'})

    # Ending if the scoring file does not contain positions (rsIDs)
    if 'chr_position' not in df.columns:
        report('No position')
        quit()

    # Headers for alleles. other_allele is optional, but should be tested if exists as we don't know which allele is the reference one.
    alleles_headers = ['effect_allele']
    if 'other_allele' in df.columns:
        alleles_headers.append('other_allele')

    if len(alleles_headers) == 1:
        report('Warning: Only 1 allele column, expect low match rate.')

    errors = []
    match = 0
    mismatch = 0

    # If rsID, just fetch the variant position and compare it
    max_request_size = None
    map_variants_func = None
    if 'rsID' in df.columns and not use_pos:
        report('Using rsIDs to validate variant positions')
        max_request_size = MAX_VARIATION_REQUEST_SIZE
        map_variants_func = map_rsids
    else:
        max_request_size = MAX_SEQUENCE_REQUEST_SIZE
        map_variants_func = map_variants_to_reference_genome

    variant_slices = sample_df(df, n_requests, max_request_size, alleles_headers, flip, errors)

    for variants in variant_slices:
        results = map_variants_func(variants, ref_genome)
        match += results['match']
        mismatch += results['mismatch']
        errors = errors + results['errors']

    report(scoring_file)
    report("Ref genome: " + ref_genome)
    report("Matches: " + str(match))
    report("Mismatches: " + str(mismatch))
    if errors:
        report("Errors:", errors)


if __name__ == "__main__":
    main()
