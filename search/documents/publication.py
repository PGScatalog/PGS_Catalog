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
            'raw': fields.TextField(analyzer='keyword'),
            'suggest': fields.CompletionField()
        }
    )
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
            'id': fields.TextField(analyzer=id_analyzer),
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
                    'id': fields.TextField(analyzer=id_analyzer),
                    'id_colon': fields.TextField(analyzer=id_analyzer),
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
                    'id': fields.TextField(analyzer=id_analyzer),
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
                            'id': fields.TextField(analyzer=id_analyzer),
                            'id_colon': fields.TextField(analyzer=id_analyzer),
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
    #    # Optional - Only used to update data and indexes
    #    related_models = [Score]
    #
    # def get_instances_from_related(self, related_instance):
    #     """If related_models is set, define how to retrieve the Publication instance from the related model."""
    #     if isinstance(related_instance, Score):
    #         return related_instance.publication
