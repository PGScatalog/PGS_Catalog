import requests
from pgs_web import constants
import logging

from core.services.errors import NotFoundError

ols_root_url = constants.USEFUL_URLS['OLS_ROOT_URL'] + '/api/ontologies/efo'
logger = logging.getLogger(__name__)


class OLSRestClient:
    """A client to fetch data from the Ontology Lookup Service REST API."""

    def __init__(self):
        self.cached_terms = {}
        self.cached_ancestors = {}

    def get_term(self, term_id):
        """Get an OLSTerm object for the given term ID. It checks if the response is correctly formatted and contains
        the expected keys. If not, it raises an Exception with the unexpected response."""
        if term_id not in self.cached_terms:
            try:
                response = requests.get(ols_root_url + '/terms?obo_id=' + term_id.replace('_', ':'))
                response.raise_for_status()
                if '_embedded' not in response.json() and 'terms' not in response.json()['_embedded']:
                    raise ValueError(f"Unexpected response for term {term_id}: {response.json()}")
                data = response.json()['_embedded']['terms']
                if len(data) == 0:
                    raise NotFoundError('No term found in OLS for id %s' % term_id)
                if len(data) == 1:
                    response = data[0]
                else:
                    logger.warning(f"Multiple terms found in OLS for id {term_id}: {data}")
                    response = data[0]
                self.cached_terms[term_id] = response
            except requests.exceptions.RequestException as e:
                print(f"Error fetching details for term {term_id}: {e}")
                raise e

        return self.cached_terms[term_id]

    def get_ancestors(self, term_id):
        """Get the ancestors of a term given its ID."""
        if term_id not in self.cached_ancestors:
            response = requests.get(f'{ols_root_url}/ancestors?id={term_id}')
            try:
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching ancestors for term {term_id}: {e}")
                raise e
            response_json = response.json()
            ols_embedded = '_embedded'
            ols_links = '_links'
            ols_next = 'next'
            if ols_embedded in response_json:
                response = response_json[ols_embedded]['terms']
                # Fetch parent data and store it
                if len(response) > 0:
                    if ols_links in response_json:
                        total_terms_count = response_json['page']['totalElements']

                        while ols_next in response_json[ols_links]:
                            next_url = response_json[ols_links][ols_next]['href']
                            response_next = requests.get(next_url)
                            response_json = response_next.json()
                            response_terms = response_json[ols_embedded]['terms']
                            response = response + response_terms

                        if total_terms_count != len(response):
                            raise ValueError(
                                f'The number of ancestors of "{term_id}" retrieved doesn\'t match the number of ancestors declared by the REST API: {total_terms_count} vs {len(response)}')
                    else:
                        raise ValueError(
                            "The script can't retrieve the parents of the trait '" + term_id + "' (" + term_id + "): the API returned " + str(
                                len(response)) + " results.")
                else:
                    raise NotFoundError("  >> WARNING: Can't find parents for the trait '" + term_id + "'.")
            self.cached_ancestors[term_id] = response

        return self.cached_ancestors[term_id]
