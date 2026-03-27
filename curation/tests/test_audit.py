from core.testing import CurationTestCase

try:
    from auditlog.models import LogEntry
    from auditlog.registry import auditlog
except RuntimeError:
    raise RuntimeError("Auditlog is not properly configured. Ensure that AUDITLOG_ENABLED is set to True, "
                       "'auditlog' is included in INSTALLED_APPS,"
                       " and 'auditlog.middleware.AuditlogMiddleware' is included in MIDDLEWARE settings.")

from catalog.models import Publication, Score, EFOTrait


class ConfigTest(CurationTestCase):

    def test_settings(self):
        from django.conf import settings
        self.assertTrue(settings.AUDITLOG_ENABLED, "AUDITLOG_ENABLED setting should be True to enable auditlog functionality.")
        self.assertIn('auditlog', settings.INSTALLED_APPS, "'auditlog' should be included in INSTALLED_APPS to enable auditlog functionality.")
        self.assertIn('auditlog.middleware.AuditlogMiddleware', settings.MIDDLEWARE, "'auditlog.middleware.AuditlogMiddleware' should be included in MIDDLEWARE to enable auditlog functionality.")

    def test_registration(self):
        self.assertTrue(auditlog.contains(Publication))
        self.assertTrue(auditlog.contains(Score))


class AuditLogPublicationTest(CurationTestCase):

    def setUp(self):
        self.publication = Publication.objects.create(num=1, date_publication='2026-01-01',
                                                      PMID=12345, journal='Test Journal', curation_status='E')

    def test_create_produces_log_entry(self):
        entries = LogEntry.objects.get_for_object(self.publication)
        self.assertTrue(entries.filter(action=LogEntry.Action.CREATE).exists())

    def test_create_entry_count(self):
        self.assertEqual(LogEntry.objects.get_for_object(self.publication).count(), 1)

    def test_create_entry_object_repr(self):
        entry = LogEntry.objects.get_for_object(self.publication).first()
        self.assertEqual(entry.object_repr, str(self.publication))

    def test_modify_publication(self):
        self.publication.curation_status = 'C'
        self.publication.save()
        entries = LogEntry.objects.get_for_object(self.publication)
        self.assertTrue(entries.filter(action=LogEntry.Action.UPDATE).exists())

        # Get the UPDATE entry and check the new value was logged
        update_entry = entries.filter(action=LogEntry.Action.UPDATE).latest('timestamp')
        self.assertIn('curation_status', update_entry.changes)
        old_value, new_value = update_entry.changes['curation_status']
        self.assertEqual(old_value, 'E')
        self.assertEqual(new_value, 'C')


class AuditLogScoreTest(CurationTestCase):

    def setUp(self):
        self.publication = Publication.objects.create(num=2, date_publication='2026-01-01',
                                                      PMID=12346, journal='Test Journal 2', curation_status='E')
        self.score = Score.objects.create(num=1, publication=self.publication, variants_number=10, name='Test Score')
        efo_traits = EFOTrait.objects.bulk_create([
            EFOTrait(id='MONDO_0043458', label='radiation injury'),
            EFOTrait(id='MONDO_0800177', label='frostbite'),
        ])
        self.score.trait_efo.set(efo_traits)

    def test_create_produces_log_entry(self):
        entries = LogEntry.objects.get_for_object(self.score)
        self.assertTrue(entries.filter(action=LogEntry.Action.CREATE).exists())

    def test_modify_score(self):
        self.score.name = 'Updated Test Score'
        self.score.save()
        entries = LogEntry.objects.get_for_object(self.score)
        self.assertTrue(entries.filter(action=LogEntry.Action.UPDATE).exists())

        # Get the UPDATE entry and check the new value was logged
        update_entry = entries.filter(action=LogEntry.Action.UPDATE).latest('timestamp')
        self.assertIn('name', update_entry.changes)
        old_value, new_value = update_entry.changes['name']
        self.assertEqual(old_value, 'Test Score')
        self.assertEqual(new_value, 'Updated Test Score')

    def test_swap_score_trait_efo(self):
        new_trait = EFOTrait.objects.create(id='MONDO_0043519', label='burn')
        old_trait = self.score.trait_efo.last()
        self.score.trait_efo.remove(old_trait)
        self.score.trait_efo.add(new_trait)
        entries = LogEntry.objects.get_for_object(self.score)
        update_entries = entries.filter(action=LogEntry.Action.UPDATE).order_by('timestamp')
        self.assertEqual(update_entries.count(), 3)  # includes first assignment in setup

        # Check removal was logged
        removal_entry = update_entries[1]  # second update (first is from setUp)
        removal_change_data = removal_entry.changes.get('trait_efo')
        self.assertIn(str(old_trait), removal_change_data.get('objects', []))
        self.assertEqual(removal_change_data.get('operation'), 'delete')

        # Check addition was logged
        add_entry = update_entries[2]
        add_change_data = add_entry.changes.get('trait_efo')
        self.assertIn(str(new_trait), add_change_data.get('objects', []))
        self.assertEqual(add_change_data.get('operation'), 'add')

    def test_dont_log_ancestries(self):
        self.score.ancestries = {"eval": {"dist": {"GME": 100}, "count": 1}, "gwas": {"dist": {"AFR": 100}, "count": 1}}
        self.score.save()
        entries = LogEntry.objects.get_for_object(self.score)
        update_entries = entries.filter(action=LogEntry.Action.UPDATE)
        self.assertFalse(update_entries.filter(changes__has_key='ancestries').exists())
