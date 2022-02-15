from django.conf import settings
from django_elasticsearch_dsl import Document, Index, fields
from search.analyzers import id_analyzer, html_strip_analyzer, name_delimiter_analyzer

from catalog.models import Publication, Score

# Name of the Elasticsearch index
INDEX = Index(settings.ELASTICSEARCH_INDEX_NAMES[__name__])

# See Elasticsearch Indices API reference for available settings
INDEX.settings(
    number_of_shards=1,
    number_of_replicas=1
)

# PGS index analyzers
id_analyzer = id_analyzer()
html_strip = html_strip_analyzer()
name_delimiter = name_delimiter_analyzer()


@INDEX.doc_type
class PublicationDocument(Document):
    """Publication elasticsearch document"""

    id = fields.TextField(
        analyzer=id_analyzer,
        fields={
            'raw': fields.TextField()
        }
    )
    title = fields.TextField(
        analyzer=name_delimiter,
        fields={
            'raw': fields.TextField()
        }
    )
    journal = fields.TextField(
        analyzer=html_strip,
        fields={
            'raw': fields.TextField()
        }
    )
    pub_year = fields.TextField(
        analyzer=html_strip,
        fields={
            'raw': fields.TextField()
        }
    )
    PMID = fields.TextField(
        analyzer=html_strip,
        fields={
            'raw': fields.TextField()
        }
    )
    firstauthor = fields.TextField(
        analyzer=html_strip,
        fields={
            'raw': fields.TextField()
        }
    )
    authors = fields.TextField(
        analyzer=html_strip,
        fields={
            'raw': fields.TextField()
        }
    )
    doi = fields.TextField(
        analyzer=html_strip,
        fields={
            'raw': fields.TextField()
        }
    )
    scores_count = fields.IntegerField()
    scores_evaluated_count = fields.IntegerField()
    publication_score = fields.ObjectField(
        properties={
            'id': fields.TextField(analyzer=id_analyzer),
            'name': fields.TextField(
                analyzer=html_strip,
                fields={
                    'raw': fields.KeywordField()
                }
            ),
            'trait_reported': fields.TextField(
                analyzer=html_strip,
                fields={
                    'raw': fields.TextField()
                }
            ),
            'trait_efo': fields.ObjectField(
                properties={
                    'id': fields.TextField(analyzer=id_analyzer),
                    'id_colon': fields.TextField(analyzer=id_analyzer),
                    'label': fields.TextField(
                        analyzer=html_strip,
                        fields={
                            'raw': fields.TextField()
                        }
                    )
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
                            'raw': fields.TextField()
                        }
                    ),
                    'trait_reported': fields.TextField(
                        analyzer=html_strip,
                        fields={
                            'raw': fields.TextField()
                        }
                    ),
                    'trait_efo': fields.ObjectField(
                        properties={
                            'id': fields.TextField(analyzer=id_analyzer),
                            'id_colon': fields.TextField(analyzer=id_analyzer),
                            'label': fields.TextField(
                                analyzer=html_strip,
                                fields={
                                    'raw': fields.TextField()
                                }
                            )
                        }
                    )
                }
            )
        }
    )


    class Django(object):
        """Inner nested class Django."""

        model = Publication  # The model associated with this Document
