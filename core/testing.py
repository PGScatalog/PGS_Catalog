from django.test import TestCase


class PGSTestCase(TestCase):
    """Base test case class for PGS Catalog tests that require database access in curation context."""
    databases = {'default', 'curation_tracker'}
