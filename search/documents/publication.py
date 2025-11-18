from django.conf import settings
from django_elasticsearch_dsl import Document, Index, fields
from search.analyzers import id_analyzer, html_strip_analyzer, name_delimiter_analyzer

from catalog.models import Publication

# Name of the Elasticsearch index
INDEX = Index(settings.ELASTICSEARCH_INDEX_NAMES[__name__])

# See Elasticsearch Indices API reference for available settings
INDEX.settings(
    number_of_shards=1,
    number_of_replicas=0
)

# PGS index analyzers
id_analyzer = id_analyzer()
html_strip = html_strip_analyzer()
name_delimiter = name_delimiter_analyzer()


@INDEX.doc_type
class PublicationDocument(Document):
    """Publication elasticsearch document"""

    id = fields.TextField(analyzer=id_analyzer)
    title = fields.TextField(analyzer=name_delimiter)
    journal = fields.TextField(index=False)
    pub_year = fields.IntegerField(index=False)
    PMID = fields.TextField(analyzer=id_analyzer)
    firstauthor = fields.TextField(analyzer=html_strip)
    authors = fields.TextField(analyzer=html_strip)
    doi = fields.TextField(analyzer=id_analyzer)
    scores_count = fields.IntegerField(index=False)
    scores_evaluated_count = fields.IntegerField(index=False)
    publication_score = fields.ObjectField(
        properties={
            'id': fields.TextField(analyzer=id_analyzer),
            'name': fields.TextField(
                analyzer=name_delimiter,
                fields={
                    'raw': fields.KeywordField()
                }
            ),
            'trait_reported': fields.TextField(analyzer=html_strip),
            'trait_efo': fields.ObjectField(
                properties={
                    'id': fields.TextField(analyzer=id_analyzer),
                    'id_colon': fields.TextField(analyzer=id_analyzer),
                    'label': fields.TextField(analyzer=html_strip)
                }
            )
        }
    )
    publication_performance = fields.ObjectField(
        properties={
            'score': fields.ObjectField(
                properties={
                    'id': fields.TextField(analyzer=id_analyzer),
                    'name': fields.TextField(
                        analyzer=name_delimiter,
                        fields={
                            'raw': fields.KeywordField()
                        }
                    )#,
                    # 'trait_reported': fields.TextField(analyzer=html_strip),
                    # 'trait_efo': fields.ObjectField(
                    #     properties={
                    #         'id': fields.TextField(analyzer=id_analyzer),
                    #         'id_colon': fields.TextField(analyzer=id_analyzer),
                    #         'label': fields.TextField(analyzer=html_strip)
                    #     }
                    # )
                }
            )
        }
    )


    class Django(object):
        """Inner nested class Django."""

        model = Publication  # The model associated with this Document
