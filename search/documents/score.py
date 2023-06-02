from django.conf import settings
from django_elasticsearch_dsl import Document, Index, fields
from search.analyzers import id_analyzer, name_delimiter_analyzer
from catalog.models import Score

# Name of the Elasticsearch index
INDEX = Index(settings.ELASTICSEARCH_INDEX_NAMES[__name__])

# See Elasticsearch Indices API reference for available settings
INDEX.settings(
    number_of_shards=1,
    number_of_replicas=1
)

# PGS index analyzer
id_analyzer = id_analyzer()
name_delimiter = name_delimiter_analyzer()


@INDEX.doc_type
class ScoreDocument(Document):
    """Score elasticsearch document"""

    id = fields.TextField(analyzer=id_analyzer)
    name = fields.TextField(
        analyzer=name_delimiter,
        fields={
            'raw': fields.KeywordField()
        }
    )
    publication = fields.ObjectField(
        properties={
            'id': fields.TextField()
        }
    )
    trait_reported = fields.TextField(
        fields={
            'raw': fields.KeywordField()
        }
    )
    trait_efo = fields.ObjectField(
        properties={
            'id': fields.TextField(),
            'label': fields.TextField()
        }
    )
    variants_number = fields.IntegerField()

    class Django(object):
        """Inner nested class Django."""

        model = Score  # The model associated with this Document
