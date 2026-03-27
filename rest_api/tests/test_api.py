from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from core.testing import CurationTestCase


class ErrorRestTest(TestCase):
    def test_nonexistingEndpoint(self):
        response = self.client.get('getAllPizzas')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class PublicationRestTest(CurationTestCase):

    # Load data in DB - Must live in the rest_api/fixtures/ directory
    fixtures = ['db_test.json']

    def test_publication(self):
        id = 'PGP000001'

        response = self.client.get(
                    reverse('getPublication', kwargs={'pgp_id': id}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], id)

    def test_all_publications(self):
        response = self.client.get(reverse('getAllPublications'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)


class ScoreRestTest(CurationTestCase):

    # Load data in DB - Must live in the rest_api/fixtures/ directory
    fixtures = ['db_test.json']

    def test_score(self):
        id = 'PGS000001'

        response = self.client.get(
                    reverse('getScore', kwargs={'pgs_id': id}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], id)

    def test_all_scores(self):
        response = self.client.get(reverse('getAllScores'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)


class GCSTRestTest(CurationTestCase):

    # Load data in DB - Must live in the rest_api/fixtures/ directory
    fixtures = ['db_test.json']

    def test_gcst(self):
        id = 'GCST001937'

        response = self.client.get(
                    reverse('pgs_score_ids_from_gwas_gcst_id', kwargs={'gcst_id': id}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, ["PGS000001","PGS000002"])
