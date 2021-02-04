from django.conf import settings
from django_elasticsearch_dsl import Document, Index, fields
from search.analyzers import name_delimiter_analyzer
from catalog.models import Publication, Score

# Name of the Elasticsearch index
INDEX = Index(settings.ELASTICSEARCH_INDEX_NAMES[__name__])

# See Elasticsearch Indices API reference for available settings
INDEX.settings(
    number_of_shards=1,
    number_of_replicas=1
)

# PGS index analyzer
name_delimiter = name_delimiter_analyzer()


@INDEX.doc_type
class ScoreDocument(Document):
    """Publication elasticsearch document"""

    id = fields.TextField()
    name = fields.TextField(
        analyzer=name_delimiter
    )
    publication = fields.ObjectField(
        properties={
            'id': fields.TextField()
        }
    )
    trait_reported = fields.TextField()
    trait_efo = fields.ObjectField(
        properties={
            'id': fields.TextField(),
            'label': fields.TextField()
        }
    )
    variants_number = fields.TextField()

    class Django(object):
        """Inner nested class Django."""

        model = Score  # The model associated with this Document
