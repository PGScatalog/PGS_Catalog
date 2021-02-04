from django.conf import settings
from django_elasticsearch_dsl import Document, Index, fields
#from elasticsearch_dsl import analysis, analyzer
from search.analyzers import html_strip_analyzer, name_delimiter_analyzer

from catalog.models import Publication, Score

# Name of the Elasticsearch index
INDEX = Index(settings.ELASTICSEARCH_INDEX_NAMES[__name__])

# See Elasticsearch Indices API reference for available settings
INDEX.settings(
    number_of_shards=1,
    number_of_replicas=1
)


html_strip = html_strip_analyzer()
name_delimiter = name_delimiter_analyzer()


@INDEX.doc_type
class PublicationDocument(Document):
    """Publication elasticsearch document"""

    id = fields.TextField()
    title = fields.TextField(
        analyzer=html_strip,
        fields={
            'raw': fields.TextField(analyzer='keyword'),
        }
    )
    journal = fields.TextField(
        analyzer=html_strip,
        fields={
            'raw': fields.TextField(analyzer='keyword'),
        }
    )
    pub_year = fields.TextField(
        analyzer=html_strip,
        fields={
            'raw': fields.TextField(analyzer='keyword'),
        }
    )
    PMID = fields.TextField(
        analyzer=html_strip,
        fields={
            'raw': fields.TextField(analyzer='keyword'),
        }
    )
    firstauthor = fields.TextField(
        analyzer=html_strip,
        fields={
            'raw': fields.TextField(analyzer='keyword'),
        }
    )
    authors = fields.TextField(
        analyzer=html_strip,
        fields={
            'raw': fields.TextField(analyzer='keyword'),
        }
    )
    doi = fields.TextField(
        analyzer=html_strip,
        fields={
            'raw': fields.TextField(analyzer='keyword'),
        }
    )
    scores_count = fields.IntegerField()
    scores_evaluated_count = fields.IntegerField()
    publication_score = fields.ObjectField(
        properties={
            'id': fields.TextField(
                analyzer=html_strip,
                fields={
                    'raw': fields.TextField(analyzer='keyword'),
                    'suggest': fields.CompletionField()
                }
            ),
            'name': fields.TextField(
                analyzer=name_delimiter,#html_strip,
                fields={
                    'raw': fields.TextField(analyzer='keyword'),
                }
            ),
            'trait_reported': fields.TextField(
                analyzer=html_strip,
                fields={
                    'raw': fields.TextField(analyzer='keyword'),
                }
            ),
            'trait_efo': fields.ObjectField(
                properties={
                    'id': fields.TextField(
                        analyzer=html_strip,
                        fields={
                            'raw': fields.TextField(analyzer='keyword'),
                            'suggest': fields.CompletionField()
                        }
                    ),
                    'label': fields.TextField(
                        analyzer=html_strip,
                        fields={
                            'raw': fields.TextField(analyzer='keyword'),
                            'suggest': fields.CompletionField()
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
                    'id': fields.TextField(
                        analyzer=html_strip,
                        fields={
                            'raw': fields.TextField(analyzer='keyword'),
                            'suggest': fields.CompletionField()
                        }
                    ),
                    'name': fields.TextField(
                        analyzer=html_strip,
                        fields={
                            'raw': fields.TextField(analyzer='keyword'),
                        }
                    ),
                    'trait_reported': fields.TextField(
                        analyzer=html_strip,
                        fields={
                            'raw': fields.TextField(analyzer='keyword'),
                        }
                    ),
                    'trait_efo': fields.ObjectField(
                        properties={
                            'id': fields.TextField(
                                analyzer=html_strip,
                                fields={
                                    'raw': fields.TextField(analyzer='keyword'),
                                    'suggest': fields.CompletionField()
                                }
                            ),
                            'label': fields.TextField(
                                analyzer=html_strip,
                                fields={
                                    'raw': fields.TextField(analyzer='keyword'),
                                    'suggest': fields.CompletionField()
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
    #    related_models = [Score]
    #
    #    def get_instances_from_related(self, related_instance):
    #        """If related_models is set, define how to retrieve the Publication instance from the related model."""
    #        if isinstance(related_instance, Score):
    #            return related_instance.publication
