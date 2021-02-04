from elasticsearch_dsl import Q
from search.documents.efo_trait import EFOTraitDocument
from search.documents.publication import PublicationDocument
from search.documents.score import ScoreDocument

class PGSSearch:
    fields = []      # fields that should be searched
    query = None     # query term(s)
    count = 0        # response count
    document = None  # ES document to use

    def search(self):
        query_settings = Q("multi_match", type="best_fields", query=self.query, fields=self.fields)
        search_query = self.document.search().query(query_settings).extra(size=20)
        response = search_query.execute()
        self.count = len(response)
        return response


class EFOTraitSearch(PGSSearch):

    def __init__(self, query):
        self.query = query
        self.fields = [
            "id^3",
            "id_colon^3",
            "label^3",
            "synonyms^2",
            "mapped_terms^2",
            # Trait category data
            "traitcategory.label",
            "traitcategory.parent",
            # Score data - direct association
            "scores_direct_associations.id",
            "scores_direct_associations.name",
            "scores_direct_associations.trait_reported",
            # Score data - child association
            "scores_child_associations.id",
            "scores_child_associations.name",
            "scores_child_associations.trait_reported",
            # Parent data
            "parent_traits.id",
            "parent_traits.id_colon",
            "parent_traits.label^2"
        ]
        self.document = EFOTraitDocument



class PublicationSearch(PGSSearch):

    def __init__(self, query):
        self.query = query
        self.fields = [
            "id",
            "title^2",
            "firstauthor^2",
            "authors",
            "PMID^2",
            "doi^2",
            # Score data - developed
            "publication_score.id",
            "publication_score.name",
            # Score data - evaluated
            "publication_performance.score.id",
            "publication_performance.score.name",
            # Score trait data
            "publication_score.trait_reported",
            "publication_score.trait_efo.id",
            "publication_score.trait_efo.id_colon",
            "publication_score.trait_efo.label"
        ]
        self.document = PublicationDocument



class ScoreSearch(PGSSearch):

    def __init__(self, query):
        self.query = query
        self.fields = [
            "id^3",
            "name",
        ]
        self.document = ScoreDocument
