from django.conf import settings
from django_elasticsearch_dsl import Document, Index, fields
from search.analyzers import id_analyzer, html_strip_analyzer, name_delimiter_analyzer
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
html_strip = html_strip_analyzer()
name_delimiter = name_delimiter_analyzer()


@INDEX.doc_type
class ScoreExtDocument(Document):
    """Score Extension elasticsearch document"""

    id = fields.TextField(analyzer=id_analyzer)
    name = fields.TextField(
        analyzer=name_delimiter,
        fields={
            'raw': fields.KeywordField()
        }
    )
    publication = fields.ObjectField(
        properties={
            'id': fields.TextField(analyzer=id_analyzer),
            'title': fields.TextField(analyzer=name_delimiter),
            'firstauthor': fields.TextField(analyzer=html_strip),
            'PMID': fields.TextField(analyzer=id_analyzer),
            'doi': fields.TextField(analyzer=id_analyzer)
        }
    )
    trait_reported = fields.TextField(analyzer=html_strip)
    trait_efo = fields.ObjectField(
        properties={
            'id': fields.TextField(analyzer=id_analyzer),
            'id_colon': fields.TextField(analyzer=id_analyzer),
            'label': fields.TextField(
                analyzer=name_delimiter,
                fields={
                    'suggest': fields.CompletionField()
                }
            ),
            'synonyms': fields.TextField(analyzer=name_delimiter),
            'mapped_terms': fields.TextField(analyzer=name_delimiter)
        }
    )

    class Django(object):
        """Inner nested class Django."""

        model = Score  # The model associated with this Document
