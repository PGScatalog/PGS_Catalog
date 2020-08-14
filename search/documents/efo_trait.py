from django.conf import settings
from django_elasticsearch_dsl import Document, Index, fields
from elasticsearch_dsl import analyzer

from catalog.models import EFOTrait_Ontology, TraitCategory, Score

# Name of the Elasticsearch index
INDEX = Index(settings.ELASTICSEARCH_INDEX_NAMES[__name__])

# See Elasticsearch Indices API reference for available settings
INDEX.settings(
    number_of_shards=1,
    number_of_replicas=1
)


html_strip = analyzer(
    'html_strip',
    tokenizer="standard",
    filter=["lowercase", "stop", "snowball", "remove_duplicates"],
    char_filter=["html_strip"]
)

@INDEX.doc_type
class EFOTraitDocument(Document):
    """EFOTrait elasticsearch document"""

    id = fields.TextField()
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
            )
        }
    )
    scores_child_associations = fields.ObjectField(
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
            )
        }
    )
    parent_traits = fields.ObjectField(
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
                }
            )
        }
    )

    class Django(object):
        """Inner nested class Django."""

        model = EFOTrait_Ontology  # The model associated with this Document
        related_models = [TraitCategory]

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, TraitCategory):
            return related_instance.efotraits_ontology.all()
