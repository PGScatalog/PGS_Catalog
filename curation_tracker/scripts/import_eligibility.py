import os
import re
import pandas as pd
import numpy as np
from curation_tracker.models import *

triage_dir = '/Users/lg10/Workspace/git/fork/PGS_GCP_development/curation_tracker/scripts/triage/'
ext = '.tsv'

tracker_db = 'curation_tracker'

eligibility_attributes = {
    'eligibility_dev_score': '1 - Develop new score?',
    'eligibility_eval_score': '1 - Evaluate existing score?',
    'eligibility_external_valid': '2: External validation (dev and eval in different sample?)',
    'eligibility_trait_matching': '3 - Trait matching',
    'eligibility_score_provided': '4 -Score provided?'
}

def add_eligibility_annotation(data):
    for pmid in data.keys():
        print(f"\n# {pmid}:")
        pub_annot = None
        try:
            pub_annot = CurationPublicationAnnotation.objects.using(tracker_db).get(PMID=pmid)
        except CurationPublicationAnnotation.DoesNotExist:
            doi = data[pmid]['doi']
            if doi:
                try:
                    pub_annot = CurationPublicationAnnotation.objects.using(tracker_db).get(doi=doi)
                except CurationPublicationAnnotation.DoesNotExist:
                    print(f"Publication with the PubMed ID: {pmid} couldn't be found in the Curation Tracker")

        if pub_annot:
            print(f"  >> Publication found")
            for field in eligibility_attributes.keys():
                if data[pmid][field]:
                    val = data[pmid][field]
                    if field == 'eligibility_trait_matching':
                        val = re.sub('\w\s\-\s','',val)

                if val not in [None,np.nan,'nan','']:
                    print(f"  - {field}: {val}")
                    setattr(pub_annot, field, val)
            pub_annot.save(using=tracker_db)
        else:
            print(f"  !! Publication NOT found")

################################################################################

def run():
    data = {}
    files = [f for f in os.listdir(triage_dir) if os.path.isfile(f'{triage_dir}{f}')]
    for filename in files:
        if filename.endswith(ext):
            print(f"\n=========================\n>> {filename}\n=========================\n")
            df = pd.read_csv(f'{triage_dir}{filename}', sep='\t')

            for index, row in df.iterrows():
                pmid = None
                doi = None
                if row['PMID'] in [None,np.nan,'nan','','TBD'] or not re.match('^\d+$',row['PMID']):
                    continue
                pmid = row['PMID']
                if row['doi'] not in [None,np.nan,'nan','','TBD']:
                    if row['doi'].startswith('10'):
                        doi = row['doi']
                    elif row['doi'].startswith('https://doi.org/'):
                        doi = row['doi'].replace('https://doi.org/','')
                    elif row['doi'].startswith('http://doi.org/'):
                        doi = row['doi'].replace('http://doi.org/','')
                data[pmid] = {'doi': doi}

                for field in eligibility_attributes.keys():
                    val = None
                    col_name = eligibility_attributes[field]
                    col_value = row[col_name]
                    if col_value not in [None,np.nan,'nan','']:
                        val = col_value
                    data[pmid][field] = val
            add_eligibility_annotation(data)
