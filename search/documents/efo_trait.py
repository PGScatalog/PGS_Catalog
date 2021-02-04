from django.conf import settings
from django_elasticsearch_dsl import Document, Index, fields
from search.analyzers import id_analyzer, html_strip_analyzer, name_delimiter_analyzer
from catalog.models import EFOTrait_Ontology, TraitCategory, Score

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
class EFOTraitDocument(Document):
    """EFOTrait elasticsearch document"""

    id = fields.TextField(
        analyzer=id_analyzer,
        fields={
            'raw': fields.TextField(analyzer='keyword'),
            'suggest': fields.CompletionField()
        }
    )
    id_colon = fields.TextField(
        analyzer=id_analyzer,
        fields={
            'raw': fields.TextField(analyzer='keyword'),
            'suggest': fields.CompletionField()
        }
    )
    label = fields.TextField(
        analyzer=html_strip,
        fields={
            'raw': fields.TextField(analyzer='keyword'),
            'suggest': fields.CompletionField()
        }
    )
    description = fields.TextField(
        analyzer=html_strip,
        fields={
            'raw': fields.TextField(analyzer='keyword'),
            'suggest': fields.CompletionField()
        }
    )
    synonyms = fields.TextField(
        analyzer=html_strip,
        fields={
            'raw': fields.TextField(analyzer='keyword'),
        }
    )
    mapped_terms = fields.TextField(
        analyzer=html_strip,
        fields={
            'raw': fields.TextField(analyzer='keyword'),
        }
    )
    url = fields.TextField(
        analyzer=html_strip,
        fields={
            'raw': fields.TextField(analyzer='keyword')
        }
    )
    traitcategory = fields.ObjectField(
        properties={
            'label': fields.TextField(
                analyzer=html_strip,
                fields={
                    'raw': fields.TextField(analyzer='keyword'),
                    'suggest': fields.CompletionField()
                }
            ),
            'parent': fields.TextField(
                analyzer=html_strip,
                fields={
                    'raw': fields.TextField(analyzer='keyword'),
                }
            )
        }
    )
    scores_direct_associations = fields.ObjectField(
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
            )
        }
    )
    scores_child_associations = fields.ObjectField(
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
            )
        }
    )
    parent_traits = fields.ObjectField(
        properties={
            'id': fields.TextField(analyzer=id_analyzer),
            'id_colon': fields.TextField(analyzer=id_analyzer),
            'label': fields.TextField(
                analyzer=html_strip,
                fields={
                    'raw': fields.TextField(analyzer='keyword'),
                }
            )
        }
    )


    class Django(object):
        """Inner nested class Django."""

        model = EFOTrait_Ontology  # The model associated with this Document
    #    # Optional - Only used to update data and indexes
    #    related_models = [Score]
    #
    # def get_instances_from_related(self, related_instance):
    #     if isinstance(related_instance, Score):
    #         return related_instance.trait_efo.all()
