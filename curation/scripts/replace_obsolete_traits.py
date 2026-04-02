import os
import sys

from catalog.models import EFOTrait
from core.services.ols_rest_client import OLSRestClient
import curation.services.efo_trait_service as efo_trait_service
import curation.services.user_service as user_service
from auditlog.context import set_extra_data

# Note: This script is intended to be run via Django's manage.py shell, e.g.:
# python manage.py shell < curation/scripts/replace_obsolete_traits.py
# It identifies obsolete traits in the database, replaces them with their specified replacements from EFO,
# and exports a list of updated score IDs for reference to be used to update the header of the scoring files.

EXPORTED_SCORE_IDS_FILENAME = 'updated_score_ids.txt'

# Get current user id from environment variable (if set) to include in auditlog extra data for traceability (optional)
current_user_id = user_service.get_current_user_id()


def replace_score_trait_in_scores(obsolete_efo_trait: EFOTrait, replacement_efo_trait: EFOTrait) -> set[str]:
    """Replaces the obsolete EFO trait with the replacement EFO trait in all associated scores.
    Returns a set of updated score IDs for reference."""
    print(f'Replacing obsolete trait {obsolete_efo_trait.id} with {replacement_efo_trait.id} in:')
    with set_extra_data({'additional_data': {'reason': 'Obsolete trait replacement'}, 'actor_id': current_user_id}):  # extra auditlog info
        updated_score_ids = efo_trait_service.replace_score_trait_in_scores(obsolete_efo_trait, replacement_efo_trait)
    print(f'  - {len(updated_score_ids)} scores: {", ".join(sorted(updated_score_ids))}')
    return updated_score_ids


def main():
    print('Starting obsolete trait replacement process...')
    ols_client = OLSRestClient()
    obsolete_traits: list[EFOTrait] = []
    updated_score_ids: set[str] = set()
    for trait_efo in EFOTrait.objects.all():
        ols_term = ols_client.get_term(trait_efo.id)
        if 'is_obsolete' in ols_term and ols_term['is_obsolete']:
            print(f'The trait "{ols_term['label']}" ({trait_efo.id}) is labelled as obsolete by EFO.')
            obsolete_traits.append(trait_efo)
            replacement_term_id = ols_term['term_replaced_by'] if 'term_replaced_by' in ols_term else None
            if not replacement_term_id:
                print(f'ALERT: No replacement term specified for obsolete trait {trait_efo.id}. Aborting.')
                return 1
            replacement_term_id = replacement_term_id.split('/')[-1]
            replacement_efo_trait = efo_trait_service.get_or_make_efo_trait(replacement_term_id)
            updated_score_ids.update(replace_score_trait_in_scores(trait_efo, replacement_efo_trait))

    print(f'Finished processing. {len(obsolete_traits)} obsolete traits were found and updated with their replacements where applicable.')

    # Export score IDs list
    with open(EXPORTED_SCORE_IDS_FILENAME, 'w') as f:
        for score_id in sorted(updated_score_ids):
            f.write(f'{score_id}\n')
    print(f'>> Exported {len(updated_score_ids)} updated score IDs to "{EXPORTED_SCORE_IDS_FILENAME}".')

    return 0


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
