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


    index_result_mutliplicity = 2
    index_example = 3


    # Tuple: ( Endpoint name | Base URL | Flag for results multiplicity | Parameter examples* )
    endpoints = [
        ('Cohorts', 'cohort/all', 1),
        ('Cohort/SYMBOL', 'cohort', 1, {'path': ['ABC','DEF']}),
        ('EFO Traits', 'trait/all', 1),
        ('EFO Trait/ID', 'trait', 0, {'path': ['EFO_0000305','EFO:0000305','efo:0000305','efo_0000305','MONDO_0007254'], 'extra_query': 'include_children=0'}),
        ('EFO Trait Search', 'trait/search', 1, {'query': [
                                                            'term=breast carcinoma', 'term=breast carcinoma&include_children=0',
                                                            'term=Cancer',
                                                            'term=OMIM:615554', 'term=OMIM:615554&exact=1', 'term=OMIM:615554&include_children=0&exact=1'
                                                          ]
        }),
        ('Performances', 'performance/all', 1),
        ('Performance metric/ID', 'performance', 0, {'path': ['PPM000001','PPM000002']}),
        ('Performances Search','performance/search', 1, {'query': ['pgs_id=PGS000001','pgs_id=PGS000002']}),
        ('Publications', 'publication/all', 1),
        ('Publicsation/ID', 'publication', 0, {'path': ['PGP000001','pgp000002']}),
        ('Publication Search', 'publication/search', 1, {'query': ['pgs_id=PGS000001','pmid=25855707']}),
        ('Sample Set Search', 'sample_set/search', 1, {'query': ['pgs_id=PGS000001','pgs_id=PGS000002']}),
        ('Releases', 'release/all', 1),
        ('Release/Date', 'release', 0, {'path': ['2019-12-18','2020-02-12']}),
        ('Release current', 'release/current', 0),
        ('Sample Set/ID', 'sample_set', 0, {'path': ['PSS000001','PSS000002']}),
        ('Sample Set Search', 'sample_set/search', 1, {'query': ['pgs_id=PGS000001','pgs_id=PGS000002']}),
        ('Sample Sets', 'sample_set/all', 1),
        ('Scores', 'score/all', 1),
        ('Score/ID', 'score', 0, {'path': ['PGS000001','pgs000002']}),
        ('Scores Search', 'score/search', 1, {'query': ['pmid=25855707','trait_id=MONDO_0007254']}),
        ('Scores IDs from a GWAS/ID', 'gwas/get_score_ids', 2, {'path': ['GCST001937','GCST004988']}),
        ('Trait Category', 'trait_category/all', 1),
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
                elif ('query' in endpoint[self.index_example]):
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
                elif ('query' in endpoint[self.index_example]):
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
                elif ('query' in endpoint[self.index_example]):
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
