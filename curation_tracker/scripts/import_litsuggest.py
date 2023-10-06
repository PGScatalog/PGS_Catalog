import os
from curation_tracker.litsuggest import litsuggest_import_to_annotation, curation_tracker_db

litsuggest_dir = '/home/florent/PGS_Catalog/Curation/Litsuggest/'

def run():
    
    files = [f for f in os.listdir(litsuggest_dir) if os.path.isfile(f'{litsuggest_dir}/{f}')]

    for filename in files:   
        if filename.startswith('litsuggest'):
            filepath = f'{litsuggest_dir}{filename}'
            print(f'Reading {filepath}...')
            annotations = litsuggest_import_to_annotation(filepath)
            for annotation in annotations:
                if not annotation.is_valid():
                    print(f'Study {annotation.annotation.PMID} is not valid: {annotation.error}')
                elif not annotation.is_importable():
                    print(f'Study {annotation.annotation.PMID} won\'t be imported: {annotation.skip_reason}')
                else:
                    print(f'Imported new study {annotation.annotation.study_name} ({annotation.annotation.PMID})')
                    annotation.save(using=curation_tracker_db)

