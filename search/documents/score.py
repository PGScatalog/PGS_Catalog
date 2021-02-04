from django.conf import settings
from django_elasticsearch_dsl import Document, Index, fields
#from elasticsearch_dsl import analysis, analyzer
from search.analyzers import name_delimiter_analyzer

from catalog.models import Publication, Score

# Name of the Elasticsearch index
INDEX = Index(settings.ELASTICSEARCH_INDEX_NAMES[__name__])

# See Elasticsearch Indices API reference for available settings
INDEX.settings(
    number_of_shards=1,
    number_of_replicas=1
)

# word_delimiter_graph_preserve_original = analysis.token_filter(
#     'word_delimiter_graph_preserve_original',
#     type="word_delimiter_graph",
#     preserve_original=True
# )
# name_delimiter = analyzer(
#     'name_delimiter',
#     tokenizer="keyword",
#     filter=["lowercase", word_delimiter_graph_preserve_original, "flatten_graph", "stop", "snowball", "remove_duplicates"]
#     #filter=[word_delimiter_graph_preserve_original, "flatten_graph", "lowercase", "stop", "snowball", "remove_duplicates"]
# )

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
