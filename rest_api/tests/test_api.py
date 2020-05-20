from django.test import TestCase, Client
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.test import RequestsClient
from catalog.models import *


class ErrorRestTest(TestCase):
    def test_nonexistingEndpoint(self):
        client = RequestsClient()
        response = self.client.get('getAllPizzas')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class PublicationRestTest(TestCase):

    def setUp(self):
        self.id = "PGP000001"
        self.date_publication='2015-04-08'
        self.publication = Publication(num=1, id=self.id, date_publication=self.date_publication)
        self.publication.save()

    def test_publication(self):
        publication = Publication.objects.get(id=self.publication.id)
        response = self.client.get(
                    reverse('getPublication', kwargs={'pgp_id': self.id}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        date_string = publication.date_publication.strftime("%Y-%m-%d")
        self.assertEqual(response.data['id'], publication.id)
        self.assertEqual(response.data['date_publication'], date_string)


class ScoreRestTest(TestCase):

    def setUp(self):
        self.id = "PGS000001"
        self.name = "PRS77_BC"

        self.publication = Publication(num=1, id='PGP000001', date_publication='2015-04-08')
        self.publication.save()
        self.score = Score(num=1, id=self.id, name=self.name, publication_id=1, variants_number=1)
        self.score.save()

    def test_score(self):
        score = Score.objects.get(id=self.score.id)
        response = self.client.get(
                    reverse('getScore', kwargs={'pgs_id': self.id}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['id'], score.id)
        self.assertEqual(response.data['name'], score.name)


class BrowseUrlTest(TestCase):
    """ Test the main URLs of the website """

    def test_urls(self):
        client = Client()
        urls = [
            '/rest/',
            '/rest/trait/all/',
            '/rest/publication/all/',
            '/rest/release/all/',
            '/rest/score/all/',
        ]
        for url in urls:
            resp = client.get(url)
            self.assertEqual(resp.status_code, 200)
