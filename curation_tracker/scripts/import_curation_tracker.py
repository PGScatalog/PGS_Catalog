import pandas as pd
import numpy as np
import re
from curation_tracker.models import *
from catalog.models import Publication

tracker_file = '/Users/lg10/Workspace/datafiles/curation/tracker/PGSCatalog_Curation_Tracker.tsv'

tracker_db = 'curation_tracker'

determined_ineligible = 'Determined ineligible'

def next_id_number(model):
    ''' Fetch the new primary key value. '''
    assigned = 1
    if len(model.objects.using(tracker_db).all()) != 0:
        assigned = model.objects.using(tracker_db).latest().pk + 1
    return assigned


def get_curator(name):
    try:
        curator = CurationCurator.objects.using(tracker_db).get(name=name)
    except CurationCurator.DoesNotExist:
        curator = CurationCurator()
        setattr(curator, 'name', name)
        curator.save(using=tracker_db)
    return curator


def get_pgs_publication(PMID,doi):
    publication = None
    if PMID:
        try:
           publication_id = Publication.objects.get(PMID=PMID)
        except Publication.DoesNotExist:
           publication = None
    if doi and not publication:
        try:
           publication = Publication.objects.get(doi=doi)
        except Publication.DoesNotExist:
           publication = None
    return publication


def get_date_released(pgp_id):
    date_released = Publication.objects.values_list('date_released', flat=True).get(id=pgp_id)
    return date_released


def add_publication(id,row):
    attributes = {
        'doi': 'doi',
        'PMID': 'PMID',
        'journal': 'Journal',
        'title': 'Title',
        'year': 'Year'
    }
    data = { 'study_name': id }
    has_pgp_id = False
    pmid = None
    doi = None
    for field in attributes.keys():
        col = attributes[field]
        val = None
        col_value = row[col]
        if field in ['PMID','year'] and re.search('^\d+$',str(col_value)):
            val = col_value
            if field == 'PMID':
                pmid = val
        if col_value not in [None,np.nan,'nan','']:
            if field in ['PMID','year'] and not re.search('^\d+$',str(col_value)):
                col_value = None
            val = col_value
            if field == 'PMID':
                pmid = val
            elif field == 'doi':
                doi = val
        if val != None:
            data[field] = val
    publication = get_pgs_publication(pmid,doi)
    if publication:
        data['pgp_id'] = publication.id
        data['journal'] = publication.journal
        data['title'] = publication.title
    if 'AuthorSub' in id:
        data['author_submission'] = True
    else:
        data['author_submission'] = False
    return data


def get_curation_attribute_values(field,col,row):
    if 'comment' in field:
        val = ''
    else:
        val = None
    col_value = row[col]
    if col_value not in [None,np.nan,'nan']:
        if 'date' in field:
            # print(f"  DATE: {col_value}")
            # DD/MM/YYYY or DD-MM-YYYY format
            if re.search('^\d{2}\D\d{2}\D\d{4}$',col_value):

                for char in ['/','-']:
                    if re.search('^\d{2}\\'+char+'\d{2}\\'+char+'\d{4}$',col_value):
                        date_list = col_value.split(char)
                        val = f"{date_list[2]}-{date_list[1]}-{date_list[0]}"
                        # print(f"  > DATE DMY: {col_value} => {val}")
                        break
            # YYYY/MM/DD format
            elif re.search('^\d{4}\/\d{2}\/\d{3}$',col_value):
                val = col_value.replace('/','-')
                # print(f"  > DATE YMD: {col_value} => {val}")
        else:
            val = col_value
    return val


def add_first_level_curation(row):
    attributes = {
        'first_level_curation_status': 'First level status',
        'first_level_date': 'First level date',
        'first_level_comment': 'First level comment'
    }
    data = {}
    curator_name = row['First level curator']
    if curator_name not in [None,np.nan,'nan','']:
        curator = get_curator(curator_name)
        data['first_level_curator'] = curator
    for field in attributes.keys():
        col = attributes[field]
        val = get_curation_attribute_values(field,col,row)
        if val != None:
            data[field] = val
    return data


def add_second_level_curation(row):
    attributes = {
        'second_level_curation_status': 'Second level status',
        'second_level_date': 'Second level date',
        'second_level_comment': 'Second level comment'
    }
    data = {}
    curator_name = row['Second level curator']
    if curator_name not in [None,np.nan,'nan','']:
        curator = get_curator(curator_name)
        data['second_level_curator'] = curator
    for field in attributes.keys():
        col = attributes[field]
        val = get_curation_attribute_values(field,col,row)
        if val != None:
            data[field] = val
    return data


def add_publication_annotation(publication,first_level_curation,second_level_curation,row):

    model = CurationPublicationAnnotation()
    model.set_annotation_ids(next_id_number(CurationPublicationAnnotation))

    # Publication
    for publication_field in ['study_name','pgp_id','doi','PMID','journal','title','year','author_submission']:
        if publication_field in publication.keys():
            setattr(model, publication_field, publication[publication_field])

    # First Level Curation
    for first_level_field in ['first_level_curator','first_level_curation_status','first_level_date','first_level_comment']:
        if first_level_field in first_level_curation.keys():
            setattr(model, first_level_field, first_level_curation[first_level_field])

    # Second Level Curation
    for second_level_field in ['second_level_curator','second_level_curation_status','second_level_date','second_level_comment']:
        if second_level_field in second_level_curation.keys():
            setattr(model, second_level_field, second_level_curation[second_level_field])


    if row['Third level curator'] not in [None,np.nan,'nan','']:
        third_level_curator = get_curator(row['Third level curator'])
        setattr(model, 'third_level_curator', third_level_curator)

    # Notes
    comments = ''
    attributes = {
        'curation_status': 'Curation_status',
        'reported_trait': 'Trait(s)',
        'gwas_and_pgs': 'GWAS + PGS',
        'comment_early': 'Early comment/Note',
        'comment_sam': 'Comments (Sam)',
        'comment_other': 'Comments (Curator/Others)'
    }
    for field in attributes.keys():
        col = attributes[field]
        if field.startswith('comment'):
            val = ''
        else:
            val = None

        col_value = row[col]
        if col_value not in [None,np.nan,'nan','']:
            val = col_value
        if val != None:
            if field.startswith('comment') and val != '':
                if comments != '':
                    comments = comments+'\n'
                comments = comments + val
        else:
            # Setup the Curation Status
            if field == 'curation_status':
                level_1_done = False
                level_2_done = False
                # L1 curation
                if 'first_level_curation_status' in first_level_curation:
                    first_level_curation_status = first_level_curation['first_level_curation_status']
                    if first_level_curation_status == 'Author-reported':
                        first_level_curation_status = 'Author submission'
                    elif first_level_curation_status in ['Curation done','Curation done (AS)',determined_ineligible]:
                        level_1_done = True
                        if first_level_curation_status == determined_ineligible:
                            val = 'Abandoned/Ineligble'
                    if first_level_curation_status == 'Author submission' and 'second_level_curation_status' in second_level_curation:
                        first_level_curation_status = 'Curation done (AS)'
                        level_1_done = True
                # L2 curation
                if 'second_level_curation_status' in second_level_curation:
                    second_level_curation_status = second_level_curation['second_level_curation_status']
                    if second_level_curation_status in ['Curation done',determined_ineligible]:
                        level_2_done = True
                        if second_level_curation_status == determined_ineligible:
                            val = 'Abandoned/Ineligble'
                if val == None:
                    if level_1_done == True:
                        if level_2_done == False:
                            val = 'Awaiting L2'
                        else:
                            val = 'Curated - Awaiting Import'
                    else:
                        val = 'Awaiting L1'

        # Add value to model
        if val != None and not field.startswith('comment'):
            setattr(model, field, val)

    if comments != '':
        setattr(model, 'comment', comments)

    # Curation status
    curation_status = model.curation_status
    if curation_status:
        if curation_status != determined_ineligible:
            setattr(model, 'eligibility', True)
        else:
            setattr(model, 'eligibility_description', determined_ineligible)

    # Release
    if 'pgp_id' in publication:
        date_released = get_date_released(publication['pgp_id'])
        if date_released:
            setattr(model, 'release_date', date_released)

    model.save(using=tracker_db)




################################################################################

def run():

    df = pd.read_csv(tracker_file, sep='\t')

    ids_list = []

    for index, row in df.iterrows():
        study_name = None
        for col in ['Name', 'doi', 'PMID']:
            if row[col] not in [None,np.nan,'nan','','TBD']:
                study_name = row[col]
                break
        print(f'{index}: {study_name}')
        if not re.search('^\w+',study_name):
            print(f'{index}: naming not found')
        if study_name in ids_list:
            print(f"- Duplicated study name: {study_name}")
            extra = 2
            new_study_name = f'{study_name}_{extra}'
            while new_study_name in ids_list:
                extra += 1
                new_study_name = f'{study_name}_{extra}'
            study_name = new_study_name
            print(f"\t=> new study name: {new_study_name}")
        ids_list.append(study_name)

        publication = add_publication(study_name,row)
        first_level_curation = add_first_level_curation(row)
        second_level_curation = add_second_level_curation(row)
        add_publication_annotation(publication,first_level_curation,second_level_curation,row)
