from django.test import TestCase


class CurationTestCase(TestCase):
    """Base test case class for PGS Catalog tests that require database access in curation context."""
    databases = {'default', 'curation_tracker'}
