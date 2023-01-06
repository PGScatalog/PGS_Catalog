from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.views import exception_handler
from rest_framework.exceptions import Throttled
from rest_framework.serializers import ValidationError
from pgs_web import constants
from pgs_web import constants_rest
from django.db.models import Prefetch, Q
from catalog.models import *
from .serializers import *

generic_defer = ['curation_notes']
related_dict = {
    'score_prefetch' : [
        Prefetch('trait_efo', queryset=EFOTrait.objects.defer('synonyms','mapped_terms').all()),
        Prefetch('samples_variants', queryset=Sample.objects.select_related('sample_age','followup_time').all().order_by('id').prefetch_related('cohorts')),
        Prefetch('samples_training', queryset=Sample.objects.select_related('sample_age','followup_time').all().order_by('id').prefetch_related('cohorts')),
    ],
    'perf_select': ['score', 'publication', 'sampleset'],
    'associated_scores_prefetch': [Prefetch('associated_scores', queryset=Score.objects.only('id','trait_efo__id').all())],
    'ontology_associated_scores_prefetch': [
                                             Prefetch('scores_direct_associations', queryset=Score.objects.only('id','trait_efo__id').all()),
                                             Prefetch('scores_child_associations', queryset=Score.objects.only('id','trait_efo__id').all())
                                           ],
    'traitcategory_prefetch': [Prefetch('traitcategory', queryset=TraitCategory.objects.only('label','efotraits__id').all())],
    'traitcategory_ontology_prefetch': [Prefetch('traitcategory', queryset=TraitCategory.objects.only('label','efotraits_ontology__id').all())],
    'efotraits_ontology_set_prefetch': [Prefetch('efotraits_ontology_set', queryset=EFOTrait_Ontology.objects.only('label','child_traits__id').all())],
    'efotraits_prefetch': [Prefetch('efotraits', queryset=EFOTrait.objects.defer('synonyms','mapped_terms').all())],
    'sample_set_prefetch' : [
                              Prefetch('sample_set', queryset=Sample.objects.only('id').all()),
                              'sample_set__sampleset',
                              Prefetch('sample_set__score_variants', queryset=Score.objects.only('id').all()),
                              Prefetch('sample_set__score_training', queryset=Score.objects.only('id').all())
                            ],
    'sampleset_samples_cohorts_prefetch': [Prefetch('sampleset__samples__cohorts', queryset=Cohort.objects.only('id','name_short','name_full').all())],
    'score_defer': [*generic_defer,'publication__curation_status','publication__curation_notes','publication__date_released','publication__authors'],
    'perf_defer': [*generic_defer,'date_released','score__ancestries','score__curation_notes','score__date_released','publication__curation_status','publication__curation_notes','publication__date_released','publication__authors'],
    'publication_defer': [*generic_defer,'curation_status']
}

def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    # Over the fixed rate limit
    if isinstance(exc, Throttled): # check that a Throttled exception is raised
        response.data = { # custom response data
            'message': 'request limit exceeded',
            'availableIn': '%d seconds'%exc.wait
        }
    # Over the maximum number of results per page (limit parameter)
    elif isinstance(exc, ValidationError):
        formatted_exc = ''
        for type in exc.detail.keys():
            if formatted_exc != '':
                formatted_exc += '; '
            formatted_exc += exc.detail[type]
        response.data = { # custom response data
            'status_code': response.status_code,
            'message': formatted_exc
        }
    elif response.status_code == status.HTTP_404_NOT_FOUND:
        response.data = { # custom response data
            'status_code': status.HTTP_404_NOT_FOUND,
            'message': 'This REST endpoint does not exist'
        }
    elif response is not None:
        response.data = { # custom response data
            'status_code': response.status_code,
            'message': str(exc)
        }
    else:
        response.data = {
            'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR,
            'message': 'Internal Server Error'
        }
    return response


def get_ids_list(object):
    ids_list = []

    # List of IDs provided in the URL
    ids = object.request.query_params.get('filter_ids')
    if ids and ids is not None:
        ids = ids.upper()
        ids_list = ids.split(',')
    # List of IDs provided in a JSON object
    elif 'filter_ids' in object.request.data:
        ids_list = [ x.upper() for x in object.request.data['filter_ids']]
    return ids_list


## Publications ##

class RestListPublications(generics.ListAPIView):
    """
    Retrieve the PGS Publications
    """
    serializer_class = PublicationExtendedSerializer

    def get_queryset(self):
        # Fetch all the Publications
        queryset = Publication.objects.defer(*related_dict['publication_defer']).all().order_by('num')

        # Filter by list of Publications IDs
        ids_list = get_ids_list(self)
        if ids_list:
            queryset = queryset.filter(id__in=ids_list)

        return queryset


class RestPublication(generics.RetrieveAPIView):
    """
    Retrieve one PGS Publication
    """

    def get(self, request, pgp_id):
        pgp_id = pgp_id.upper()
        try:
            queryset = Publication.objects.defer(*related_dict['publication_defer']).get(id=pgp_id)
        except Publication.DoesNotExist:
            queryset = None
        serializer = PublicationExtendedSerializer(queryset,many=False)
        return Response(serializer.data)


class RestPublicationSearch(generics.ListAPIView):
    """
    Retrieve the Publication(s) using query
    """
    serializer_class = PublicationExtendedSerializer

    def get_queryset(self):
        queryset = Publication.objects.defer(*related_dict['publication_defer']).all().order_by('num')
        params = 0

        # Search by Score ID
        pgs_id = self.request.query_params.get('pgs_id')
        if pgs_id and pgs_id is not None:
            pgs_id = pgs_id.upper()
            try:
                score = Score.objects.only('id','publication__id').select_related('publication').get(id=pgs_id)
                queryset = queryset.filter(id=score.publication.id)
                params += 1
            except Score.DoesNotExist:
                queryset = []

        # Search by Author
        author = self.request.query_params.get('author')
        if author and author is not None:
            queryset = queryset.filter(authors__icontains=author)
            params += 1

        # Search by Pubmed ID
        pmid = self.request.query_params.get('pmid')
        if pmid and pmid.isnumeric():
            queryset = queryset.filter(PMID=pmid)
            params += 1

        if params == 0:
            queryset = []


        return queryset


## Scores ##

class RestListScores(generics.ListAPIView):
    """
    Retrieve the Polygenic Scores
    """
    serializer_class = ScoreSerializer

    def get_queryset(self):
        # Fetch all the Scores
        queryset = Score.objects.defer(*related_dict['score_defer']).select_related('publication').all().prefetch_related(*related_dict['score_prefetch']).order_by('num')

        # Filter by list of Score IDs
        ids_list = get_ids_list(self)
        if ids_list:
            queryset = queryset.filter(id__in=ids_list)

        return queryset


class RestScore(generics.RetrieveAPIView):
    """
    Retrieve one Polygenic Score (PGS)
    """

    def get(self, request, pgs_id):
        pgs_id = pgs_id.upper()
        try:
            queryset = Score.objects.defer(*related_dict['score_defer']).select_related('publication').prefetch_related(*related_dict['score_prefetch']).get(id=pgs_id)
        except Score.DoesNotExist:
            queryset = None
        serializer = ScoreSerializer(queryset,many=False)
        return Response(serializer.data)


class RestScoreSearch(generics.ListAPIView):
    """
    Search the Polygenic Score(s) using query
    """
    serializer_class = ScoreSerializer

    def get_queryset(self):
        queryset = Score.objects.defer(*related_dict['score_defer']).select_related('publication').all().prefetch_related(*related_dict['score_prefetch']).order_by('num')
        params = 0

        # Search by list of Score IDs
        pgs_ids = self.request.query_params.get('pgs_ids')
        if pgs_ids and pgs_ids is not None:
            pgs_ids = pgs_ids.upper()
            pgs_ids_list = pgs_ids.split(',')
            queryset = queryset.filter(id__in=pgs_ids_list)
            params += 1

        # Search by Pubmed ID
        pmid = self.request.query_params.get('pmid')
        if pmid and pmid.isnumeric():
            queryset = queryset.filter(publication__PMID=pmid)
            params += 1

        # Search by PGP ID
        pgp_id = self.request.query_params.get('pgp_id')
        if pgp_id and pgp_id is not None:
            pgp_id = pgp_id.upper()
            queryset = queryset.filter(publication__id=pgp_id)
            params += 1

        # Search by Trait ID
        trait_id = self.request.query_params.get('trait_id')
        if trait_id and trait_id is not None:
            trait_id = trait_id.upper().replace(':','_')
            queryset = queryset.filter(trait_efo__id=trait_id)
            params += 1

        if params == 0:
            queryset = []

        return queryset


## Performance metrics ##

class RestListPerformances(generics.ListAPIView):
    """
    Retrieve the PGS Performance Metrics
    """
    serializer_class = PerformanceSerializer

    def get_queryset(self):
        # Fetch all the Performances
        queryset = Performance.objects.defer(*related_dict['perf_defer']).select_related(*related_dict['perf_select']).all().prefetch_related('sampleset__samples',*related_dict['sampleset_samples_cohorts_prefetch'],'performance_metric').order_by('num')

        # Filter by list of Performance IDs
        ids_list = get_ids_list(self)
        if ids_list:
            queryset = queryset.filter(id__in=ids_list)

        return queryset


class RestPerformanceSearch(generics.ListAPIView):
    """
    Retrieve the Performance metric(s) using query
    """
    serializer_class = PerformanceSerializer


    def get_queryset(self):

        queryset = Performance.objects.defer(*related_dict['perf_defer']).select_related(*related_dict['perf_select']).all().prefetch_related('sampleset__samples',*related_dict['sampleset_samples_cohorts_prefetch'],'performance_metric').order_by('num')
        params = 0

        # Search by Score ID
        pgs_id = self.request.query_params.get('pgs_id')
        if pgs_id and pgs_id is not None:
            pgs_id = pgs_id.upper()
            queryset = queryset.filter(score__id=pgs_id)
            params += 1

        # Search by PGP ID
        pgp_id = self.request.query_params.get('pgp_id')
        if pgp_id and pgp_id is not None:
            pgp_id = pgp_id.upper()
            queryset = queryset.filter(publication__id=pgp_id)
            params += 1

        # Search by Pubmed ID
        pmid = self.request.query_params.get('pmid')
        if pmid and pmid.isnumeric():
            queryset = queryset.filter(publication__PMID=pmid)
            params += 1

        if params == 0:
            queryset = []

        return queryset


class RestPerformance(generics.RetrieveAPIView):
    """
    Retrieve one Performance metric
    """

    def get(self, request, ppm_id):
        ppm_id = ppm_id.upper()
        try:
            queryset = Performance.objects.defer(*related_dict['perf_defer']).select_related(*related_dict['perf_select']).prefetch_related('sampleset__samples',*related_dict['sampleset_samples_cohorts_prefetch'],'performance_metric').get(id=ppm_id)
        except Performance.DoesNotExist:
            queryset = None
        serializer = PerformanceSerializer(queryset,many=False)
        return Response(serializer.data)


## Traits ##

class RestListEFOTraits(generics.ListAPIView):
    """
    Retrieve all the EFO Traits
    """

    def get_queryset(self):
        include_parents = self.get_include_parents_param()
        include_children_pgs_ids = self.get_include_children_pgs_ids_param()

        if include_parents or include_children_pgs_ids:
            queryset = EFOTrait_Ontology.objects.all().prefetch_related(*related_dict['ontology_associated_scores_prefetch'], *related_dict['traitcategory_ontology_prefetch']).order_by('label').distinct()
        else:
            queryset = EFOTrait.objects.all().prefetch_related(*related_dict['associated_scores_prefetch'], *related_dict['traitcategory_prefetch']).order_by('label')

        # Filter by list of Score IDs
        ids_list = get_ids_list(self)
        if ids_list:
            if include_parents:
                queryset = queryset.filter(Q(id__in=ids_list) | Q(child_traits__id__in=ids_list))
            else:
                queryset = queryset.filter(id__in=ids_list)

        return queryset


    def get_serializer_class(self):
        ''' Overwrite default method: use different serializer depending on the URL parameter '''
        if self.get_include_children_pgs_ids_param():
            return EFOTraitOntologySerializer
        else:
            return EFOTraitExtendedSerializer


    def get_include_children_pgs_ids_param(self):
        ''' Fetch the "include_child_associated_pgs_ids" parameter and return True if it is set to 1 '''
        param_include_children_pgs_ids = self.request.query_params.get('include_child_associated_pgs_ids')
        if (not param_include_children_pgs_ids or param_include_children_pgs_ids == None) and 'include_child_associated_pgs_ids' in self.request.data:
            param_include_children_pgs_ids = self.request.data['include_child_associated_pgs_ids']

        if param_include_children_pgs_ids == '1' or param_include_children_pgs_ids == 1:
            return True
        return False


    def get_include_parents_param(self):
        ''' Fetch the "include_parents" parameter and return True if it is set to 1 '''
        param_include_parents = self.request.query_params.get('include_parents')
        if (not param_include_parents or param_include_parents == None) and 'include_parents' in self.request.data:
            param_include_parents = self.request.data['include_parents']

        if param_include_parents == '1' or param_include_parents == 1:
            return True
        return False


class RestEFOTrait(generics.RetrieveAPIView):
    """
    Retrieve one EFO Trait
    """

    def get(self, request, trait_id):
        trait_id = trait_id.upper().replace(':', '_')

        # Check if the trait ID belongs to a source where the prefix is not in upper case (e.g. Orphanet)
        trait_id_lc = trait_id.lower()
        for source in constants.TRAIT_SOURCE_TO_REPLACE:
            source_lc = source.lower()
            if trait_id_lc.startswith(source_lc):
                trait_id = trait_id_lc.replace(source_lc,source)
                break

        try:
            queryset = EFOTrait_Ontology.objects.prefetch_related(*related_dict['ontology_associated_scores_prefetch'], *related_dict['traitcategory_ontology_prefetch']).get(id=trait_id)
        except EFOTrait_Ontology.DoesNotExist:
            queryset = None

        # 'include_children' parameter
        include_children = True
        param_include_children = self.request.query_params.get('include_children')
        if param_include_children != None:
            if  param_include_children == '0' or param_include_children == 0:
                include_children = False

        if include_children:
           serializer = EFOTraitOntologyChildSerializer(queryset,many=False)
        else:
           serializer = EFOTraitOntologySerializer(queryset,many=False)

        return Response(serializer.data)


class RestEFOTraitSearch(generics.ListAPIView):
    """
    Retrieve the EFO Trait(s) using query
    """
    serializer_class = EFOTraitOntologySerializer

    def get_queryset(self):

        queryset = EFOTrait_Ontology.objects.all().prefetch_related(*related_dict['ontology_associated_scores_prefetch'], *related_dict['traitcategory_ontology_prefetch']).order_by('label').distinct()

        # 'include_children' parameter
        include_children = True
        param_include_children = self.request.query_params.get('include_children')
        if param_include_children != None:
            if  param_include_children == '0' or param_include_children == 0:
                include_children = False

        # 'exact' parameter
        exact_term = False
        param_exact_term = self.request.query_params.get('exact')
        if param_exact_term != None:
            if  param_exact_term == '1' or param_exact_term == 1:
                exact_term = True

        # Search by trait term
        term = self.request.query_params.get('term')
        if term and term is not None:
            if include_children:
                if exact_term:
                    queryset = queryset.filter(
                        Q(id=term) | Q(label=term) | Q(synonyms__regex='(^|\| )'+term+'( \||$)') |
                        Q(mapped_terms__regex='(^|\| )'+term+'( \||$)') | Q(traitcategory__label=term) |
                        Q(parent_traits__id=term) | Q(parent_traits__label=term)
                    )
                else:
                    queryset = queryset.filter(
                        Q(id=term) | Q(label__icontains=term) | Q(synonyms__icontains=term) | Q(mapped_terms__icontains=term) |
                        Q(traitcategory__label__icontains=term) | Q(parent_traits__id=term) | Q(parent_traits__label__icontains=term)
                    )
            else:
                if exact_term:
                    queryset = queryset.filter(
                        Q(id=term) | Q(label=term) | Q(synonyms__regex='(^|\| )'+term+'( \||$)') |
                        Q(mapped_terms__regex='(^|\| )'+term+'( \||$)') | Q(traitcategory__label=term)
                    )
                else:
                    queryset = queryset.filter(
                        Q(id=term) | Q(label__icontains=term) | Q(synonyms__icontains=term) | Q(mapped_terms__icontains=term) |
                        Q(traitcategory__label__icontains=term)
                    )
        else:
            queryset = []
        return queryset


## Trait Categories ##

class RestListTraitCategories(generics.ListAPIView):
    """
    Retrieve all the Trait categories
    """
    queryset = TraitCategory.objects.defer('parent','colour').all().prefetch_related(*related_dict['efotraits_prefetch']).order_by('label')
    serializer_class = TraitCategorySerializer


## Samples / Sample Sets ##

class RestListSampleSets(generics.ListAPIView):
    """
    Retrieve all the Cohorts
    """
    queryset = SampleSet.objects.all().prefetch_related('samples', 'samples__cohorts').order_by('id')
    serializer_class = SampleSetSerializer

    def get_queryset(self):
        # Fetch all the SampleSets
        queryset = SampleSet.objects.all().prefetch_related('samples', 'samples__cohorts').order_by('id')

        # Filter by list of SampleSet IDs
        ids_list = get_ids_list(self)
        if ids_list:
            queryset = queryset.filter(id__in=ids_list)

        return queryset


class RestSampleSet(generics.RetrieveAPIView):
    """
    Retrieve one Sample Set
    """

    def get(self, request, pss_id):
        pss_id = pss_id.upper()
        try:
            queryset = SampleSet.objects.prefetch_related('samples', 'samples__cohorts').get(id=pss_id)
        except SampleSet.DoesNotExist:
            queryset = None
        serializer = SampleSetSerializer(queryset,many=False)
        return Response(serializer.data)


class RestSampleSetSearch(generics.ListAPIView):
    """
    Retrieve the Sample Set(s) using query
    """
    serializer_class = SampleSetSerializer

    def get_queryset(self):

        queryset = []

        # Search by Score ID
        pgs_id = self.request.query_params.get('pgs_id')
        # Search by PGP ID
        pgp_id = self.request.query_params.get('pgp_id')
        # Search by Pubmed ID
        pmid = self.request.query_params.get('pmid')

        if (pgs_id and pgs_id is not None) or (pgp_id and pgp_id is not None) or (pmid and pmid.isnumeric()):
            filters = {}
            if pgs_id and pgs_id is not None:
                pgs_id = pgs_id.upper()
                filters['score__id'] = pgs_id

            if pgp_id and pgp_id is not None:
                pgp_id = pgp_id.upper()
                filters['publication__id'] = pgp_id

            if pmid and pmid.isnumeric():
                filters['publication__PMID'] = pmid

            perfs = Performance.objects.only('score_id','publication_id','sampleset_id').select_related('sampleset').filter(**filters).prefetch_related('sampleset__samples',*related_dict['sampleset_samples_cohorts_prefetch'])
            for perf in perfs:
                sampleset = perf.sampleset
                if not sampleset in queryset:
                    queryset.append(sampleset)
            queryset.sort(key=lambda x: x.id, reverse=False)

        return queryset


## Cohorts ##

class RestListCohorts(generics.ListAPIView):
    """
    Retrieve all the Cohorts
    """
    serializer_class = CohortExtendedSerializer

    def get_queryset(self):
        queryset = Cohort.objects.all().prefetch_related(*related_dict['sample_set_prefetch']).order_by('name_short')

        # 'fetch_all' parameter: fetch released and non released Cohorts
        fetch_all_cohorts = False
        param_fetch_all = self.request.query_params.get('fetch_all')
        if (not param_fetch_all or param_fetch_all == None) and 'fetch_all' in self.request.data:
            param_fetch_all = self.request.data['fetch_all']

        if param_fetch_all == '1' or param_fetch_all == 1:
            fetch_all_cohorts = True

        # 'filter_ids' parameter: fetch the cohorts from the list of cohort short names
        names_list = get_ids_list(self)

        # Filter the query depending on the parameters used
        if names_list:
            names_list = r'^('+'|'.join(names_list)+')$'
            if fetch_all_cohorts:
                queryset = queryset.filter(name_short__iregex=names_list, released=True)
            else:
                queryset = queryset.filter(name_short__iregex=names_list)
        elif fetch_all_cohorts:
            queryset = queryset.filter(released=True)

        return queryset


class RestCohorts(generics.ListAPIView):
    """
    Retrieve Cohort(s)
    """
    serializer_class = CohortExtendedSerializer

    def get_queryset(self):

        # Fetch Cohort model(s)
        try:
            cohort_symbol = self.kwargs['cohort_symbol']
            # Database filtering
            queryset = Cohort.objects.filter(name_short__iexact=cohort_symbol, released=True).prefetch_related(*related_dict['sample_set_prefetch'])
        except Cohort.DoesNotExist:
            queryset = []
        return queryset


## Releases ##

class RestListReleases(generics.ListAPIView):
    """
    Retrieve all the Release information
    """
    queryset = Release.objects.all().order_by('-date')
    serializer_class = ReleaseSerializer


class RestRelease(generics.RetrieveAPIView):
    """
    Retrieve one Release information
    """

    def get(self, request, release_date):
        try:
            queryset = Release.objects.get(date=release_date)
        except Release.DoesNotExist:
            queryset = None
        serializer = ReleaseSerializer(queryset,many=False)
        return Response(serializer.data)


class RestCurrentRelease(generics.RetrieveAPIView):
    """
    Retrieve the current Release information
    """
    def get(self, request):
        queryset = Release.objects.order_by('-date').first()
        serializer = ReleaseSerializer(queryset,many=False)
        return Response(serializer.data)


##### Extra endpoints #####

class RestGCST(APIView):
    """
    Retrieve all the Polygenic Score IDs using a given GWAS study (GCST)
    """

    def get(self, request, gcst_id):
        gcst_id = gcst_id.upper()
        samples = Sample.objects.filter(source_GWAS_catalog=gcst_id).distinct()

        try:
            scores = Score.objects.only('id').filter(samples_variants__in=samples).distinct()
        except Score.DoesNotExist:
            scores = []

        pgs_scores = [score.id for score in scores]

        return Response(pgs_scores)


class RestInfo(generics.RetrieveAPIView):
    """
    Return diverse information related to the REST API and the PGS Catalog
    """

    def get(self, request):

        release = Release.objects.only('date').order_by('-date').first()
        # Mainly to pass the tests as there is no data (and no release) in them
        if release:
            release_date = release.date
        else:
            release_date = "NA"

        latest_release = {
            'date': release_date,
            'scores': Score.objects.count(),
            'publications': Publication.objects.count(),
            'traits': EFOTrait.objects.count()
        }

        data = {
            'rest_api': constants_rest.PGS_REST_API[0],
            'latest_release': latest_release,
            'citation': constants.PGS_CITATION,
            'ensembl_version': constants.ENSEMBL_VERSION,
            'terms_of_use': constants.USEFUL_URLS['TERMS_OF_USE']
        }

        return Response(data)


class RestApiVersions(generics.RetrieveAPIView):
    """
    Return information about all the REST API versions
    """

    def get(self, request):

        versions = constants_rest.PGS_REST_API
        current = versions.pop(0)
        formatted_data = { 'current': current, 'previous': versions }

        return Response(formatted_data)


class RestAncestryCategories(generics.RetrieveAPIView):
    """
    Return the list of ancestry categories
    """

    def get(self, request):
        data = {}
        mappings = {}
        for category, id in constants.ANCESTRY_MAPPINGS.items():
            if not id in mappings:
                mappings[id] = set()
            mappings[id].add(category)

        for id, d_category in constants.ANCESTRY_LABELS.items():
            if id in mappings:
                categories_list = list(mappings[id])
            else:
                categories_list = [d_category]
            data[id] = {
                'display_category': d_category,
                'categories': sorted(categories_list)
            }
        sorted_data = dict(sorted(data.items()))
        return Response(sorted_data)
