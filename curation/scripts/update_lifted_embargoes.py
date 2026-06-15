import os
import sys

import requests
from datetime import datetime

from auditlog.context import set_extra_data
from django.db import transaction

from catalog.models import Publication
from curation.services import user_service
from curation_tracker.models import CurationPublicationAnnotation


# Fetches publications with "Embargo Lifted - Awaiting Release" from the curation tracker and updates the corresponding
# publication model in the catalog database with the information from EuropePMC.


def rest_api_call_to_epmc(query):
    payload = {'format': 'json', 'query': query}
    result = requests.get('https://www.ebi.ac.uk/europepmc/webservices/rest/search', params=payload)
    result = result.json()
    result = result['resultList']['result'][0]
    return result


def main():
    # Get current user id from environment variable (if set) to include in auditlog extra data for traceability (optional)
    current_user_id = user_service.get_current_user_id()

    lifted_embargoes_annotations = CurationPublicationAnnotation.objects.filter(curation_status='Embargo Lifted - Awaiting Release')

    print(f'Found {lifted_embargoes_annotations.count()} publications with lifted embargoes awaiting release:')

    with transaction.atomic():
        for annotation in lifted_embargoes_annotations:
            print(f'\nProcessing annotation {annotation.id} for publication with PMID {annotation.PMID} and DOI {annotation.doi}...')
            pgp_id = annotation.pgp_id
            if not pgp_id:
                print(f' - Annotation {annotation.id} has no associated PGP ID, skipping.')
                continue
            publication = Publication.objects.get(id=pgp_id)

            if publication.curation_status == 'C':
                print(f' - Publication {publication.id} already has curation status "C", skipping.')
                continue

            pmid = annotation.PMID
            doi = annotation.doi

            result = None
            if pmid:
                result = rest_api_call_to_epmc(f'ext_id:{pmid}')
            elif doi:
                result = rest_api_call_to_epmc(f'doi:{doi}')

            if result:
                firstauthor = result['authorString'].split(',')[0]
                authors = result['authorString']
                title = result['title'].strip()
                date_publication = result['firstPublicationDate']
                doi = result['doi']
                print(f"# firstauthor:{firstauthor}")
                print(f"# authors:{authors}")
                print(f"# title:{title}")
                print(f"# date_publication:{date_publication}")
                print(f"# DOI:{doi}")
                if result['pubType'] == 'preprint':
                    journal = result['bookOrReportDetails']['publisher']
                else:
                    journal = result['journalTitle']
                print(f"# journal:{journal}")

                publication.firstauthor = firstauthor
                publication.PMID = pmid
                publication.authors = authors
                publication.title = title
                publication.date_publication = date_publication
                publication.journal = journal
                publication.doi = doi
                publication.curation_status = 'C'
                with set_extra_data({
                    'additional_data': {'reason': 'Metadata update from EuropePMC after study publication'},
                    'actor_id': current_user_id}
                ):
                    publication.save()

                date_object = datetime.strptime(date_publication, '%Y-%m-%d')
                print(
                    f"\n# Scoring file citation:\n#citation={firstauthor} et al. {journal} ({date_object.year}). doi:{doi}")

                print(f'Updated publication {publication.id}.')

            else:
                print(f'Can\'t find a result on EuropePMC for the publication: {pmid}')


def run():
    try:
        sys.exit(main())
    except Exception as e:
        print(f'Error: {e}')
        sys.exit(1)


if os.path.basename(sys.argv[0]) != 'manage.py':
    raise EnvironmentError("This script must be run via Django's manage.py shell")
else:
    run()
