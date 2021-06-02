from datetime import date
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
        self.date_pub = date.today()
        self.new_publication = Publication.objects.create(num=1, id=self.id, date_publication=self.date_pub)

    def test_publication(self):
        publication = Publication.objects.get(id=self.id)

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

        new_publication = Publication.objects.create(num=2, id='PGP000002', date_publication=date.today())
        self.new_score = Score.objects.create(num=1, id=self.id, name=self.name, publication_id=new_publication.num, variants_number=1)

    def test_score(self):
        score = Score.objects.get(id=self.id)
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
            '/rest/cohort/all/',
            '/rest/sample_set/all/',
            '/rest/info/',
            '/rest/api_versions/',
            '/rest/ancestry_categories/'
        ]
        for url in urls:
            resp = client.get(url)
            self.assertEqual(resp.status_code, 200)
