import csv
import requests
from pgs_web import constants
from catalog.models import Publication
from curation_tracker.models import CurationPublicationAnnotation
from typing import List
from io import TextIOWrapper
from django.core.files.uploadedfile import InMemoryUploadedFile

pgs_db = 'default'
curation_tracker_db = 'curation_tracker'


class CurationPublicationAnnotationImport:
    """Wrapper class for CurationPublicationAnnotation for providing additional transient attributes"""
    error: str | None
    skip_reason: str | None
    annotation: CurationPublicationAnnotation
    triage_info: dict

    def __init__(self, model: CurationPublicationAnnotation | None = None):
        self.annotation = model or CurationPublicationAnnotation()
        self.error = None
        self.skip_reason = None
        self.triage_info = {}

    def to_dict(self) -> dict:
        values = annotation_to_dict(self.annotation)
        values['error'] = self.error
        values['skip_reason'] = self.skip_reason
        return values

    def is_valid(self) -> bool:
        """Should be used before saving"""
        return self.error == None

    def is_importable(self) -> bool:
        return self.skip_reason == None

    def __next_id_number(self) -> int:
        assigned = 1
        if len(CurationPublicationAnnotation.objects.using(curation_tracker_db).all()) != 0:
            assigned = CurationPublicationAnnotation.objects.using(curation_tracker_db).latest().pk + 1
        return assigned

    def save(self, *args, **kwargs) -> CurationPublicationAnnotation:
        """Set the identifiers and save the contained CurationPublicationAnnotation object"""
        annotation = self.annotation
        if annotation.num == None:
            annotation.set_annotation_ids(self.__next_id_number())
        annotation.save(*args, **kwargs)
        return annotation


class ImportException(Exception):
    pass


def get_pgs_publication(pmid):
    publication = None
    try:
        publication = Publication.objects.get(PMID=pmid)
    except Publication.DoesNotExist:
        publication = None
    return publication


def assert_study_doesnt_exist(pmid):
    """
    Checks if the study is already present as a Publication or CurationPublicationAnnotation. If yes, throws an ImportException.
    """
    if Publication.objects.using(pgs_db).filter(PMID=pmid).exists():
        raise ImportException(f'Study {pmid} already exists in the PGS Catalog database')
    if CurationPublicationAnnotation.objects.using(curation_tracker_db).filter(PMID=pmid).exists():
        raise ImportException(f'Study annotation {pmid} already exists in the Curation Tracker database')


def get_publication_info_from_epmc(pmid) -> dict:
    payload = {'format': 'json'}
    query = f'ext_id:{pmid}'
    payload['query'] = query
    result = requests.get(constants.USEFUL_URLS['EPMC_REST_SEARCH'], params=payload)
    result = result.json()
    results_list = result['resultList']['result']
    info = {'PMID': pmid}
    if results_list:
        result = results_list[0]
        info['doi'] = result.get('doi')
        info['year'] = result.get('pubYear')
        info['authors'] = result.get('authorString')
        info['journal'] = result.get('journalTitle')
        info['title'] = result.get('title')
        info['publication_date'] = result.get('firstPublicationDate')
    else:
        raise ImportException("This pubmed ID returned no result")
    return info


def get_publication_info_from_epmc_doi(doi) -> dict:
    payload = {'format': 'json'}
    query = f'doi:{doi}'
    payload['query'] = query
    result = requests.get(constants.USEFUL_URLS['EPMC_REST_SEARCH'], params=payload)
    result = result.json()
    results_list = result['resultList']['result']
    info = {'doi': doi}
    if results_list:
        result = results_list[0]
        info['PMID'] = result.get('pmid')
        info['year'] = result.get('pubYear')
        info['authors'] = result.get('authorString')
        info['journal'] = result.get('journalTitle')
        info['title'] = result.get('title')
        info['publication_date'] = result.get('firstPublicationDate')
    else:
        raise ImportException("This DOI returned no result")
    return info


def get_next_unique_study_name(study_name):
    unique_name = study_name
    for existing_study_name in CurationPublicationAnnotation.objects.using(curation_tracker_db).filter(
            study_name__startswith=study_name):
        name_elements = existing_study_name.split('_')
        name_stub = name_elements[0]
        name_index = 0
        if len(name_elements) > 1:
            last_element = name_elements[-1]
            if last_element.isnumeric():
                name_index = int(last_element)
        name_index += 1
        unique_name = name_stub + '_' + name_index

    return unique_name


def create_new_annotation(publication_info) -> CurationPublicationAnnotation:
    model = CurationPublicationAnnotation()
    for attr in ['PMID', 'journal', 'doi', 'title', 'year', 'publication_date']:
        value = publication_info.get(attr, None)
        setattr(model, attr, value)

    authors = publication_info.get('authors', None)
    if authors is None:
        authors = 'NoAuthor N'  # last char so the string has the same format as a regular authors string

    model.study_name = '-'.join(authors.split(',')[0].split(' ')[:-1]) \
                       + publication_info.get('year', 'NoDate')

    return model


def annotation_import_to_dict(annotation_import: CurationPublicationAnnotationImport) -> dict:
    d = dict()
    for attr in ['error', 'skip_reason']:
        d[attr] = getattr(annotation_import, attr)
    d['model'] = annotation_to_dict(annotation_import.annotation)
    return d


def annotation_to_dict(model: CurationPublicationAnnotation) -> dict:
    model_dict = dict()
    for attr in ['PMID', 'study_name', 'doi', 'journal', 'title', 'year', 'eligibility', 'comment',
                 'eligibility_dev_score', 'eligibility_eval_score', 'eligibility_description',
                 'first_level_curation_status', 'curation_status',
                 'publication_date']:
        model_dict[attr] = getattr(model, attr)
    return model_dict


def dict_to_annotation_import(d: dict) -> CurationPublicationAnnotationImport:
    model_import = CurationPublicationAnnotationImport(CurationPublicationAnnotation())
    if 'error' in d:
        model_import.error = d['error']
        del d['error']
    if 'skip_reason' in d:
        model_import.skip_reason = d['skip_reason']
        del d['skip_reason']
    if 'triage_info' in d:
        model_import.triage_info = d['triage_info']
    model_dict = d['model']
    for k in model_dict.keys():
        setattr(model_import.annotation, k, model_dict[k])
    return model_import


def check_study_name(study_name: str, imported_study_names: list[str]) -> str:
    """ Check that the study_name is unique. Otherwise, it will add incremental number as suffix """
    queryset = CurationPublicationAnnotation.objects.using(curation_tracker_db).filter(study_name=study_name).count()
    if queryset:
        sn_list = imported_study_names + list(
            CurationPublicationAnnotation.objects.using(curation_tracker_db).values_list('study_name', flat=True))
        num = 2
        new_study_name = f'{study_name}_{num}'
        while new_study_name in sn_list:
            num += 1
            new_study_name = f'{study_name}_{num}'
        study_name = new_study_name
    return study_name


def _litsuggest_IO_to_annotation_imports(litsuggest_file) -> List[CurationPublicationAnnotationImport]:
    models = []
    reader = csv.DictReader(litsuggest_file, delimiter='\t')
    imported_study_names = []
    for row in reader:
        if not row['pmid']:
            break  # litsuggest files might contain a lot of empty rows after the relevant ones
        pmid = str(int(row['pmid']))
        try:
            triage_decision = row['triage.decision']
            if not triage_decision:
                raise ImportException(f'Missing triage decision for {pmid}')

            assert_study_doesnt_exist(pmid)
            study_epmc_info = get_publication_info_from_epmc(pmid)
            annotationModel = create_new_annotation(study_epmc_info)
            study_name = check_study_name(annotationModel.study_name, imported_study_names)
            annotationModel.study_name = study_name
            imported_study_names.append(study_name)

            triage_note = row['triage.note']
            annotationModel.eligibility_description = triage_note

            annotation_import = CurationPublicationAnnotationImport(annotationModel)
            annotation_import.triage_info = {
                'triage_decision': triage_decision,
                'triage_note': triage_note,
                'PMID': pmid
            }

            match triage_decision:
                case 'New PGS':
                    annotationModel.eligibility = True
                    annotationModel.eligibility_dev_score = 'y'
                    annotationModel.eligibility_eval_score = 'n'
                    if isinstance(triage_note, str) and 'request score' in triage_note:
                        annotationModel.first_level_curation_status = 'Contact author'
                    annotationModel.curation_status = 'Awaiting L1'
                case 'TBD':
                    # annotationModel.eligibility = True
                    annotationModel.first_level_curation_status = 'Awaiting access'
                case 'PGS Relevant':
                    annotationModel.eligibility = False
                    annotationModel.eligibility_dev_score = None
                    annotationModel.eligibility_eval_score = None
                    annotationModel.first_level_curation_status = 'Determined ineligible'
                    annotationModel.curation_status = 'Abandoned/Ineligible'
                case 'Not PGS':
                    # Do not import (used for negatives training)
                    annotation_import.annotation.PMID = pmid
                    annotation_import.skip_reason = 'Not PGS'
                case 'Evaluated PGS':
                    annotationModel.eligibility_dev_score = 'n'
                    annotationModel.eligibility_eval_score = 'y'
                case _:
                    raise ImportException(f'Unexpected triage decision: {triage_decision}')

            models.append(annotation_import)
        except ImportException as e:
            annotation_import = CurationPublicationAnnotationImport(CurationPublicationAnnotation())
            annotation_import.annotation.PMID = pmid
            annotation_import.error = str(e)
            models.append(annotation_import)

    return models


def litsuggest_filename_to_annotation_imports(litsuggest_file_name: str) -> List[CurationPublicationAnnotationImport]:
    with open(litsuggest_file_name, 'r') as litsuggest_file:
        return _litsuggest_IO_to_annotation_imports(litsuggest_file)


def litsuggest_fileupload_to_annotation_imports(litsuggest_file_upload: InMemoryUploadedFile) -> List[CurationPublicationAnnotationImport]:
    file_wrapper = TextIOWrapper(litsuggest_file_upload.file)
    return _litsuggest_IO_to_annotation_imports(file_wrapper)
