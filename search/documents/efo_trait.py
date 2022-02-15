from django.conf import settings
from django_elasticsearch_dsl import Document, Index, fields
from search.analyzers import id_analyzer, html_strip_analyzer, name_delimiter_analyzer, ngram_analyzer
from catalog.models import EFOTrait_Ontology, TraitCategory, Score

# Name of the Elasticsearch index
INDEX = Index(settings.ELASTICSEARCH_INDEX_NAMES[__name__])

# See Elasticsearch Indices API reference for available settings
INDEX.settings(
    number_of_shards=1,
    number_of_replicas=1,
    max_ngram_diff=7
)

# PGS index analyzers
id_analyzer = id_analyzer()
html_strip = html_strip_analyzer()
name_delimiter = name_delimiter_analyzer()
ngram_analyzer = ngram_analyzer()


@INDEX.doc_type
class EFOTraitDocument(Document):
    """EFOTrait elasticsearch document"""

    id = fields.TextField(
        analyzer=id_analyzer,
        fields={
            'raw': fields.TextField()
        }
    )
    id_colon = fields.TextField(
        analyzer=id_analyzer,
        fields={
            'raw': fields.TextField()
        }
    )
    label = fields.TextField(
        analyzer=name_delimiter,
        fields={
            'raw': fields.TextField(),
            'suggest': fields.CompletionField()
        }
    )
    label_ngram = fields.TextField(
        analyzer=ngram_analyzer,
        fields={
            'raw': fields.TextField()
        }
    )
    description = fields.TextField(
        analyzer=html_strip,
        fields={
            'raw': fields.TextField()
        }
    )
    synonyms = fields.TextField(
        analyzer=name_delimiter,
        fields={
            'raw': fields.TextField()
        }
    )
    synonyms_list = fields.TextField(
        analyzer=ngram_analyzer,
        fields={
            'raw': fields.TextField(),
            'suggest': fields.CompletionField()
        }
    )
    mapped_terms = fields.TextField(
        analyzer=html_strip,
        fields={
            'raw': fields.TextField()
        }
    )
    url = fields.TextField(
        analyzer=html_strip,
        fields={
            'raw': fields.TextField()
        }
    )
    traitcategory = fields.ObjectField(
        properties={
            'label': fields.TextField(
                analyzer=name_delimiter,
                fields={
                    'raw': fields.TextField()
                }
            ),
            'parent': fields.TextField(
                analyzer=name_delimiter,
                fields={
                    'raw': fields.TextField()
                }
            )
        }
    )
    scores_direct_associations = fields.ObjectField(
        properties={
            'id': fields.TextField(analyzer=id_analyzer),
            'name': fields.TextField(
                analyzer=name_delimiter,
                fields={
                    'raw': fields.KeywordField()
                }
            ),
            'trait_reported': fields.TextField(
                analyzer=html_strip,
                fields={
                    'raw': fields.TextField()
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
                    'raw': fields.TextField()
                }
            ),
            'trait_reported': fields.TextField(
                analyzer=html_strip,
                fields={
                    'raw': fields.TextField()
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
                    'raw': fields.TextField()
                }
            )
        }
    )

    def prepare_label_ngram(self, instance):
        return instance.label


    class Django(object):
        """Inner nested class Django."""

        model = EFOTrait_Ontology  # The model associated with this Document
