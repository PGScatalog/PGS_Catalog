from django.test import TestCase, Client

class BrowseUrlTest(TestCase):
    """ Test the main URLs of the website """
    client = Client()

    def test_urls(self):
        urls = [
            '/',
            '/about/',
            '/browse/scores/',
            '/browse/traits/',
            '/browse/studies/',
            '/browse/sample_set/',
            '/docs/',
            '/docs/ancestry/',
            '/downloads/',
            '/latest_release/',
            '/rest/',
            '/robots.txt'
        ]
        self.url_response(urls, 200)


    def test_urls_permanent_redirection(self):
        urls = [
            '/browse/all/'
        ]
        self.url_response(urls, 301)


    def test_urls_redirection(self):
        urls = [
            '/docs/curation',
            '/submit/',
            '/template/current'
        ]
        self.url_response(urls, 302)


    def url_response(self,urls,code):
        for url in urls:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, code)
