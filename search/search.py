from elasticsearch_dsl import Q
from search.documents.efo_trait import EFOTraitDocument
from search.documents.publication import PublicationDocument
from search.documents.score import ScoreDocument


class PGSSearch:
    query_fields = []    # searched fields
    display_fields = []  # returned fields for display
    query = None         # query term(s)
    count = 0            # response count
    document = None      # ES document to use

    def __init__(self, query):
        self.query = str(query).lower()


    def best_fields_query(self,result_size=20):
        '''
        Build a multi-match 'best_fields' query.
        # Params:
        - result_size: maximum size of the results list (defaut: 20)
        # Returns: list of ES responses
        '''
        query_settings = Q("multi_match", type="best_fields", query=self.query, fields=self.query_fields)
        search_query = self.document.search().query(query_settings).extra(size=result_size)
        # Limit the fields returned for display
        if len(self.display_fields):
            search_query = search_query.source(self.display_fields)
        response = search_query.execute()
        return response


    def suggest_query(self,suggest_fields):
        '''
        Build a suggest query. It can groups several suggest queries to run in 1 execution
        # Params:
        - suggest_fields: list of fields to query
        # Returns: list of ES responses
        '''
        search_query = self.document.search()
        for keyword in suggest_fields:
            search_query = search_query.suggest(keyword, self.query, completion={'field': keyword+'.suggest'})
        search_query = search_query.source(self.display_fields)
        response = search_query.execute()
        return response


    def search(self):
        '''
        Main search call for the Search page
        # Returns: list of ES responses
        '''
        response = self.best_fields_query()
        self.count = len(response)
        return response


    def search_all(self):
        '''
        Search all the results
        # Returns: list of ES responses
        '''
        response = self.best_fields_query(result_size=10000)
        self.count = len(response)
        return response


    def suggest(self):
        '''
        Search call for the Autocomplete form.
        It combines 2 types of searches: "suggest" and "best_fields"
        # Returns: list of ES responses
        '''
        responses_list = set() # List of distinct suggested terms
        labels_with_case = {}  # Save the trait labels in their original cases (e.g. BMI)
        labels_ids = {}        # Link between the suggested terms and the trait label
        responses = []         # List of results to display (suggested terms + trait labels)
        self.display_fields = ['label','synonyms_list']
        suggest_fields = ['label','synonyms_list']
        self.query_fields = ['label_ngram','synonyms_list']

        ## Suggests ##

        # Suggest - build query (group the suggest queries to run in 1 execution)
        response = self.suggest_query(suggest_fields)

        # Suggest - parse query results
        for keyword in suggest_fields:
            if len(response.suggest[keyword]):
                for entry in response.suggest[keyword][0]['options']:
                    suggested_term = str(entry.text)
                    suggestion = suggested_term.lower()
                    labels_with_case[suggestion] = suggested_term
                    source_id = str(entry._source.label)
                    if suggestion not in responses_list:
                        responses_list.add(suggestion)
                        labels_ids[suggestion] = source_id
        for response in sorted(list(responses_list)):
            responses.append({'id': labels_ids[response], 'label': labels_with_case[response]})

        ## Best match ##
        response = self.best_fields_query(10)

        # Response - ES score - fetch best score
        best_score = 0
        for entry in response:
            es_score = entry.meta.score
            if best_score == 0:
                best_score = es_score

        # Extract information from the ES results
        for entry in response:
            es_score = entry.meta.score
            # Skip if the ES score is low compared to the best ES score
            if es_score < (best_score/2):
                continue

            suggested_term = str(entry.label)
            suggestion = suggested_term.lower()
            labels_with_case[suggestion] = suggested_term

            label = suggestion
            # Fetch synonym entry if the query doesn't match the trait label
            if self.query not in suggestion:
                for synonym in entry.synonyms_list:
                    if self.query in synonym.lower():
                        label = synonym
                        break
            if suggestion not in responses_list and label.lower() not in responses_list:
                responses.append({'id': labels_with_case[suggestion], 'label': label})
        return responses



class EFOTraitSearch(PGSSearch):

    def __init__(self, query):
        super().__init__(query)
        self.query_fields = [
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
        self.display_fields = [
            'id',
            'label',
            'description',
            'traitcategory.label',
            # Score data - direct association
            'scores_direct_associations.id',
            'scores_direct_associations.trait_reported',
            # Score data - child association
            'scores_child_associations.id',
            'scores_child_associations.trait_reported'
        ]
        self.document = EFOTraitDocument



class PublicationSearch(PGSSearch):

    def __init__(self, query):
        super().__init__(query)
        self.query_fields = [
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
        self.display_fields = [
            'id',
            'title',
            'firstauthor',
            'pub_year',
            'journal',
            'PMID',
            'doi',
            'scores_count',
            'scores_evaluated_count'
        ]
        self.document = PublicationDocument



class ScoreSearch(PGSSearch):

    def __init__(self, query):
        super().__init__(query)
        self.query_fields = [
            "id^3",
            "name"
        ]
        self.display_fields = [
            'id',
            'name',
            'variants_number',
            'trait_reported',
            'trait_efo',
            'publication'
        ]
        self.document = ScoreDocument
