from django.test import TestCase, Client

class BrowseUrlTest(TestCase):
    """ Test the main URLs of the website """

    def test_urls(self):
        client = Client()
        urls = [
            '/',
            '/about/',
            '/browse/all/',
            '/browse/traits/',
            '/browse/studies/',
            '/browse/sample_set/',
            '/docs/',
            '/downloads/',
            '/rest/',
            '/robots.txt'
        ]
        for url in urls:
            resp = client.get(url)
            self.assertEqual(resp.status_code, 200)

    def test_urls_redirection(self):
        client = Client()

        urls = [
            '/docs/curation',
            '/template/current'
        ]
        for url in urls:
            resp = client.get(url)
            self.assertEqual(resp.status_code, 302)
