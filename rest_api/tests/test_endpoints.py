from rest_framework.test import APITestCase
from django.conf import settings
import os, re, time
from catalog.models import *

class BrowseEndpointTest(APITestCase):
    """ Test the REST endpoints """

    # Load data in DB - Must live in the rest_api/fixtures/ directory
    fixtures = ['db_test.json']

    # Change throttle rates for the tests
    rate4test = '200/min'
    settings.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = { 'anon': rate4test, 'user': rate4test }

    # Base URL of the server
    server = '/rest/'

    fake_examples = {'string': 'ABC123CDE', 'integer': '00001', 'date': '1990-01-01'}
    empty_resp = ['{}', '{"size":0,"count":0,"next":null,"previous":null,"results":[]}', '[]']
    default_search = ['pgs_id=PGS000001','pgs_id=PGS000002','pgp_id=PGP000001','pmid=25855707']

    # Data example
    filter_ids = 'filter_ids'
    cohorts_list = ['ABC','DEF']
    traits_list = ['EFO_0000305','EFO:0000305','efo:0000305','efo_0000305','MONDO_0007254']
    performances_list = ['PPM000001','PPM000002']
    publications_list = ['PGP000001','pgp000002']
    sampleset_list = ['PSS000001','PSS000002']
    scores_list = ['PGS000001','pgs000002']

    index_result_mutliplicity = 2
    index_example = 3

    # Tuple: ( Endpoint name | Base URL | Flag for results multiplicity | Parameter examples* )
    endpoints = [
        # Cohort endpoints
        ('Cohorts', 'cohort/all', 1),
        ('Cohorts', 'cohort/all', 1, {'query': [filter_ids+'='+','.join(cohorts_list)]}),
        ('Cohort/SYMBOL', 'cohort', 1, {'path': cohorts_list}),
        # Trait endpoints
        ('EFO Traits', 'trait/all', 1),
        ('EFO Traits', 'trait/all', 1, {'query': [filter_ids+'='+','.join(traits_list)]}),
        ('EFO Trait/ID', 'trait', 0, {'path': traits_list, 'extra_query': 'include_children=0'}),
        ('EFO Trait Search', 'trait/search', 1, {'query': ['term=breast carcinoma', 'term=breast carcinoma&include_children=0',
                                                           'term=Cancer',
                                                           'term=OMIM:615554', 'term=OMIM:615554&exact=1', 'term=OMIM:615554&include_children=0&exact=1']
        }),
        ('Trait Category', 'trait_category/all', 1),
        # Performance Metrics endpoints
        ('Performances', 'performance/all', 1),
        ('Performances', 'performance/all', 1, {'query': [filter_ids+'='+','.join(performances_list)]}),
        ('Performance metric/ID', 'performance', 0, {'path': performances_list}),
        ('Performances Search','performance/search', 1, {'query': default_search}),
        # Publication endpoints
        ('Publications', 'publication/all', 1),
        ('Publications', 'publication/all', 1, {'query': [filter_ids+'='+','.join(publications_list)]}),
        ('Publicsation/ID', 'publication', 0, {'path': publications_list}),
        ('Publication Search', 'publication/search', 1, {'query': ['pgs_id=PGS000001','pmid=25855707']}),
        # Release endpoints
        ('Releases', 'release/all', 1),
        ('Release/Date', 'release', 0, {'path': ['2019-12-18','2020-02-12']}),
        ('Release current', 'release/current', 0),
        # Sample Set endpoints
        ('Sample Set/ID', 'sample_set', 0, {'path': sampleset_list}),
        ('Sample Set Search', 'sample_set/search', 1, {'query': default_search}),
        ('Sample Sets', 'sample_set/all', 1),
        ('Sample Sets', 'sample_set/all', 1, {'query': [filter_ids+'='+','.join(sampleset_list)]}),
        # Score endpoints
        ('Scores', 'score/all', 1),
        ('Scores', 'score/all', 1, {'query': [filter_ids+'='+','.join(scores_list)]}),
        ('Score/ID', 'score', 0, {'path': scores_list}),
        ('Scores Search', 'score/search', 1, {'query': ['pmid=25855707','trait_id=MONDO_0007254','pgp_id=PGP000001']}),
        # Other endpoints
        ('Scores IDs from a GWAS/ID', 'gwas/get_score_ids', 2, {'path': ['GCST001937','GCST004988']}),
        ('Info', 'info', 0),
        ('API versions', 'api_versions', 0),
        ('Ancestry categories', 'ancestry_categories', 0)
    ]


    def send_request(self, url):
        """ Send REST API request and check the reponse status code """
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode("utf-8")
        for empty_content in self.empty_resp:
            self.assertNotEqual(content, empty_content)


    def get_empty_response(self, url, index):
        """ Send REST API request and check the reponse status code """
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content.decode("utf-8"), self.empty_resp[index])


    def get_not_found_response(self, url):
        """ Send REST API request on non existing endpoint and check reponse status code """
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)


    def get_paginated_response(self, url):
        """ Send REST API request with limit and offset parameters, and check the reponse status code """
        resp = self.client.get(url+'?limit=20&offset=20')
        self.assertEqual(resp.status_code, 200)


    def test_endpoints(self):
        """ Test the status code of each endpoint """
        for endpoint in self.endpoints:
            url_endpoint = self.server+endpoint[1]
            # print(f'# {endpoint[0]}')

            if len(endpoint) > self.index_example:
                # Endpoint with parameter within the URL path
                if ('path' in endpoint[self.index_example]):
                    for example in endpoint[self.index_example]['path']:
                        request = url_endpoint+'/'+example
                        self.send_request(request)
                        if 'extra_query' in endpoint[self.index_example]:
                            request_2 = request+'?'+endpoint[self.index_example]['extra_query']
                            self.send_request(request_2)
                # Endpoint with parameter as query
                if ('query' in endpoint[self.index_example]):
                    for example in endpoint[self.index_example]['query']:
                        self.send_request(url_endpoint+'?'+example)
            else:
                self.send_request(url_endpoint)
                if endpoint[self.index_result_mutliplicity]:
                    self.get_paginated_response(url_endpoint)


    def test_endpoints_with_slash(self):

        """ Test the status code of each endpoint, with a trailing slash """
        for endpoint in self.endpoints:
            url_endpoint = self.server+endpoint[1]+'/'

            if len(endpoint) > self.index_example:
                # Endpoint with parameter within the URL path
                if ('path' in endpoint[self.index_example]):
                    for example in endpoint[self.index_example]['path']:
                        request = url_endpoint+example+'/'
                        self.send_request(request)
                        if 'extra_query' in endpoint[self.index_example]:
                            request_2 = request+'?'+endpoint[self.index_example]['extra_query']
                            self.send_request(request_2)
                # Endpoint with parameter as query
                if ('query' in endpoint[self.index_example]):
                    for example in endpoint[self.index_example]['query']:
                        self.send_request(url_endpoint+'?'+example)
            else:
                self.send_request(url_endpoint)
                if endpoint[self.index_result_mutliplicity]:
                    self.get_paginated_response(url_endpoint)


    def test_empty_endpoints(self):
        """ Test the status code and empty response of each endpoint listed above """
        for endpoint in self.endpoints:
            url_endpoint = self.server+endpoint[1]+'/'
            ex = None

            if len(endpoint) > self.index_example:
                # Endpoint with parameter within the URL path
                if ('path' in endpoint[self.index_example]):
                    ex = endpoint[self.index_example]['path'][0]

                    # Endpoint with parameter as query
                if ('query' in endpoint[self.index_example]):
                        ex_full = endpoint[self.index_example]['query'][0]
                        ex_content = ex_full.split('=')
                        url_endpoint += '?'+ex_content[0]+'='
                        ex = ex_content[1]

                if ex:
                    if re.match("^\d+$",ex):
                        url_endpoint += self.fake_examples['integer']
                    elif re.match("^\d{4}-\d{2}-\d{2}$", ex):
                        url_endpoint += self.fake_examples['date']
                    else:
                        url_endpoint += self.fake_examples['string']
                    self.get_empty_response(url_endpoint, endpoint[self.index_result_mutliplicity])


    def test_endpoint_not_found(self):
        """ Test an endpoint that doens't exist """
        self.get_not_found_response(self.server+'chocolate')
