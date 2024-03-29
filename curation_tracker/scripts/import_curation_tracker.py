import pandas as pd
import numpy as np
import re
from curation_tracker.models import *
from curation_tracker.admin import check_study_name
from catalog.models import Publication

tracker_file = '/home/florent/Workspace/PGS_Curation_Tracker/PGSCatalog_Curation_Tracker_2.tsv'

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
           publication = Publication.objects.get(PMID=PMID) #FIXME publication_id -> publication
        except Publication.DoesNotExist:
           publication = None
    if doi and not publication:
        try:
           publication = Publication.objects.get(doi=doi)
        except Publication.DoesNotExist:
           publication = None
    return publication


def get_info_from_epmc(pmid,doi,is_author_submission):
    study_name = None
    journal_name = None
    payload = {'format': 'json'}
    if pmid and re.match('^\d+$', str(pmid)):
        query = f'ext_id:{pmid}'
    else:
        query = f'doi:{doi}'
    payload['query'] = query
    result = requests.get(constants.USEFUL_URLS['EPMC_REST_SEARCH'], params=payload)
    result = result.json()
    results_list = result['resultList']['result']
    if results_list:
        result = results_list[0]
        year = result['firstPublicationDate'].split('-')[0]
        firstauthor = None
        if 'authorString' in result:
            firstauthor = result['authorString'].split(' ')[0]
        else:
            firstauthor = 'NoName'
        study_name = firstauthor+year

        if 'journalTitle' in result:
            journal_name = result['journalTitle']

        if is_author_submission:
            study_name = study_name+'_AuthorSub'
        
    return {
        'study_name': study_name,
        'journal_name': journal_name
    }


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
    if 'AuthorSub' in id:
        data['author_submission'] = True
    else:
        data['author_submission'] = False
    publication = get_pgs_publication(pmid,doi)
    if publication:
        data['pgp_id'] = publication.id
        data['journal'] = publication.journal
        data['title'] = publication.title
    elif str(id).startswith('10.') or re.search('^\d+$',str(id)):
        info = get_info_from_epmc(pmid,doi,data['author_submission'])
        new_study_name = info.get('study_name')
        data['journal'] = info.get('journal_name')
        if new_study_name:
            new_study_name = check_study_name(new_study_name)
            print(f"\t>>> NEW STUDY NAME: {new_study_name} (old: {id})")
            data['study_name'] = new_study_name

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

    # Notes
    comments = ''
    attributes = {
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

        # Add value to model
        if val != None and not field.startswith('comment'):
            setattr(model, field, val)

    if comments != '':
        setattr(model, 'comment', comments)


    # Curation Status
    curation_status = None
    if 'Curation_status' in row.keys():
        cs_value = row['Curation_status']
        if cs_value not in [None,np.nan,'nan','',' ']:
            curation_status = cs_value
    level_1_done = False
    level_2_done = False
    # L1 curation
    if 'first_level_curation_status' in first_level_curation:
        first_level_curation_status = first_level_curation['first_level_curation_status']
        if first_level_curation_status == 'Author Submission' and 'second_level_curation_status' in second_level_curation:
            first_level_curation_status = 'Curation done (AS)'
            first_level_curation['first_level_curation_status'] = first_level_curation_status
        if first_level_curation_status in ['Curation done','Curation done (AS)',determined_ineligible]:
            level_1_done = True
            if first_level_curation_status == determined_ineligible:
                curation_status = 'Abandoned/Ineligible'
        elif first_level_curation_status == 'Pending author response':
            curation_status = 'Pending author response'

    # L2 curation
    if 'second_level_curation_status' in second_level_curation:
        second_level_curation_status = second_level_curation['second_level_curation_status']
        if second_level_curation_status in ['Curation done',determined_ineligible]:
            level_2_done = True
            if second_level_curation_status == determined_ineligible:
                curation_status = 'Abandoned/Ineligible'
    # Missing L2 curation
    else:
        if level_1_done == True:
            second_level_curation_status = None
            if curation_status in ['Released','Curated - Awaiting Import','Imported - Awaiting Release','Retired','Embargoed']:
                second_level_curation_status = 'Curation done'
            elif curation_status not in ['Abandoned/Ineligible','Pending author response']:
                second_level_curation_status = 'Awaiting curation'
            if second_level_curation_status:
                second_level_curation['second_level_curation_status'] = second_level_curation_status

    # L3 curation
    if curation_status == None:
        if level_1_done == True:
            if level_2_done == False:
                curation_status = 'Awaiting L2'
            else:
                curation_status = 'Curated - Awaiting Import'
        else:
            curation_status = 'Awaiting L1'
    if curation_status != None:
        setattr(model, 'curation_status', curation_status)

    # First Level Curation
    for first_level_field in ['first_level_curator','first_level_curation_status','first_level_date','first_level_comment']:
        if first_level_field in first_level_curation.keys():
            setattr(model, first_level_field, first_level_curation[first_level_field])

    # Second Level Curation
    for second_level_field in ['second_level_curator','second_level_curation_status','second_level_date','second_level_comment']:
        if second_level_field in second_level_curation.keys():
            setattr(model, second_level_field, second_level_curation[second_level_field])

    # Third Level Curation
    if row['Third level curator'] not in [None,np.nan,'nan','']:
        third_level_curator = get_curator(row['Third level curator'])
        setattr(model, 'third_level_curator', third_level_curator)

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

    ids_list = set()

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
        ids_list.add(study_name)

        publication = add_publication(study_name,row)
        first_level_curation = add_first_level_curation(row)
        second_level_curation = add_second_level_curation(row)
        add_publication_annotation(publication,first_level_curation,second_level_curation,row)
