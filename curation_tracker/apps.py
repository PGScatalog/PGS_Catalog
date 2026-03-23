from django.apps import AppConfig

from pgs_web import settings


class CurationTrackerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'curation_tracker'

    def ready(self):

        if settings.AUDITLOG_ENABLED:
            # Registering models with auditlog for change tracking
            # Although it would be recommended to register models in catalog/models.py, it is safer to do it here as
            # the auditlog table in located in the curation_tracker DB
            self.register_models_with_auditlog()

    def register_models_with_auditlog(self):
        """Registers models with auditlog for change tracking."""
        import logging
        logging.getLogger(__name__).info("Registering models with auditlog for change tracking.")
        print("Registering models with auditlog for change tracking.")
        from auditlog.registry import auditlog
        from catalog.models import Publication, Score

        auditlog.register(Score, m2m_fields={"trait_efo"}, exclude_fields={"ancestries"})
        auditlog.register(Publication)
