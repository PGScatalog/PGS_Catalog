from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import exception_handler
from rest_framework.exceptions import Throttled
from rest_framework.serializers import ValidationError
from django.db.models import Prefetch, Q
from catalog.models import *
from .serializers import *

generic_defer = ['curation_notes','date_released']
related_dict = {
    'score_prefetch' : [
        Prefetch('trait_efo', queryset=EFOTrait.objects.defer('synonyms','mapped_terms').all()),
        Prefetch('samples_variants', queryset=Sample.objects.select_related('sample_age','followup_time').all().order_by('id').prefetch_related('cohorts')),
        Prefetch('samples_training', queryset=Sample.objects.select_related('sample_age','followup_time').all().order_by('id').prefetch_related('cohorts')),
    ],
    'perf_select': ['score', 'publication', 'sampleset'],
    'publication_score_prefetch': [Prefetch('publication_score', queryset=Score.objects.only('id','publication__id').all())],
    'publication_performance_prefetch': [Prefetch('publication_performance', queryset=Performance.objects.only('score__id','publication__id').select_related('score'))],
    'associated_scores_prefetch': [Prefetch('associated_scores', queryset=Score.objects.only('id','trait_efo__id').all())],
    'ontology_associated_scores_prefetch': [
                                             Prefetch('scores_direct_associations', queryset=Score.objects.only('id','trait_efo__id').all()),
                                             Prefetch('scores_child_associations', queryset=Score.objects.only('id','trait_efo__id').all())
                                           ],
    'traitcategory_prefetch': [Prefetch('traitcategory', queryset=TraitCategory.objects.only('label','efotraits__id').all())],
    'traitcategory_ontology_prefetch': [Prefetch('traitcategory', queryset=TraitCategory.objects.only('label','efotraits_ontology__id').all())],
    'efotraits_ontology_set_prefetch': [Prefetch('efotraits_ontology_set', queryset=EFOTrait_Ontology.objects.only('label','child_traits__id').all())],
    'efotraits_prefetch': [Prefetch('efotraits', queryset=EFOTrait.objects.defer('synonyms','mapped_terms').all())],
    'score_defer': [*generic_defer,'publication__curation_status','publication__curation_notes','publication__date_released','publication__authors'],
    'perf_defer': [*generic_defer,'score__curation_notes','score__date_released','publication__curation_status','publication__curation_notes','publication__date_released','publication__authors'],
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


## Publications ##

class RestListPublications(generics.ListAPIView):
    """
    Retrieve all the PGS Publications
    """
    queryset = Publication.objects.defer(*related_dict['publication_defer']).all().prefetch_related(*related_dict['publication_score_prefetch'],*related_dict['publication_performance_prefetch']).order_by('num')
    serializer_class = PublicationExtendedSerializer


class RestPublication(generics.RetrieveAPIView):
    """
    Retrieve one PGS Publication
    """

    def get(self, request, pgp_id):
        pgp_id = pgp_id.upper()
        try:
            queryset = Publication.objects.defer(*related_dict['publication_defer']).prefetch_related(*related_dict['publication_score_prefetch']).get(id=pgp_id)
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
        queryset = Publication.objects.all().prefetch_related(*related_dict['publication_score_prefetch']).order_by('num')
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
        if pmid and pmid is not None:
            queryset = queryset.filter(PMID=pmid)
            params += 1

        if params == 0:
            queryset = []


        return queryset


## Scores ##

class RestListScores(generics.ListAPIView):
    """
    Retrieve all the PGS Scores
    """
    queryset = Score.objects.defer(*related_dict['score_defer']).select_related('publication').all().prefetch_related(*related_dict['score_prefetch']).order_by('num')
    serializer_class = ScoreSerializer


class RestScore(generics.RetrieveAPIView):
    """
    Retrieve one PGS Score
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
    Search the PGS Score(s) using query
    """
    serializer_class = ScoreSerializer

    def get_queryset(self):
        """
        Optionally restricts the returned purchases to a given user,
        by filtering against one or serveral query parameters in the URL.
        """
        queryset = Score.objects.defer(*related_dict['score_defer']).select_related('publication').all().prefetch_related(*related_dict['score_prefetch'])
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
        if pmid and pmid is not None:
            queryset = queryset.filter(publication__PMID=pmid)
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
    Retrieve all the PGS Performance Metrics
    """
    queryset = Performance.objects.defer(*related_dict['perf_defer']).select_related(*related_dict['perf_select']).all().prefetch_related('sampleset__samples','sampleset__samples__cohorts','performance_metric').order_by('num')
    serializer_class = PerformanceSerializer


class RestPerformanceSearch(generics.ListAPIView):
    """
    Retrieve the Performance metric(s) using query
    """
    serializer_class = PerformanceSerializer

    def get_queryset(self):

        queryset = Performance.objects.defer(*related_dict['perf_defer']).select_related(*related_dict['perf_select']).all().prefetch_related('sampleset__samples','sampleset__samples__cohorts','performance_metric').order_by('num')

        # Search by Score ID
        pgs_id = self.request.query_params.get('pgs_id')
        if pgs_id and pgs_id is not None:
            pgs_id = pgs_id.upper()
            try:
                queryset = queryset.filter(score__id=pgs_id)
            except Score.DoesNotExist:
                queryset = []
        else:
            queryset = []

        return queryset


class RestPerformance(generics.RetrieveAPIView):
    """
    Retrieve one Performance metric
    """

    def get(self, request, ppm_id):
        ppm_id = ppm_id.upper()
        try:
            queryset = Performance.objects.defer(*related_dict['perf_defer']).select_related(*related_dict['perf_select']).prefetch_related('sampleset__samples','sampleset__samples__cohorts','performance_metric').get(id=ppm_id)
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
        queryset = EFOTrait.objects.all().prefetch_related(*related_dict['associated_scores_prefetch'], *related_dict['traitcategory_prefetch']).order_by('label')

        # include_parents parameter
        if self.get_include_parents_param():
            queryset = EFOTrait_Ontology.objects.all().prefetch_related(*related_dict['ontology_associated_scores_prefetch'], *related_dict['traitcategory_ontology_prefetch']).order_by('label').distinct()
        return queryset

    def get_serializer_class(self):
        ''' Overwrite default method: use different serializer depending on the URL parameter '''
        if self.get_include_parents_param():
            return EFOTraitOntologySerializer
        else:
            return EFOTraitExtendedSerializer

    def get_include_parents_param(self):
        ''' Fetch the "include_parents" parameter and return True if it is set to 1 '''
        param_include_parents = self.request.query_params.get('include_parents')
        if param_include_parents != None:
            if  param_include_parents == '1' or param_include_parents == 1:
                return True
        return False


class RestEFOTrait(generics.RetrieveAPIView):
    """
    Retrieve one EFO Trait
    """

    def get(self, request, trait_id):
        trait_id = trait_id.upper().replace(':', '_')

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
        if pgs_id and pgs_id is not None:
            pgs_id = pgs_id.upper()
            try:
                perfs = Performance.objects.select_related('sampleset').filter(score__id=pgs_id).prefetch_related('sampleset__samples','sampleset__samples__cohorts')
                for perf in perfs.all():
                    sampleset = perf.sampleset
                    if not sampleset in queryset:
                        queryset.append(sampleset)
                        queryset.sort(key=lambda x: x.id, reverse=False)
            except Score.DoesNotExist:
                queryset = []
        else:
            queryset = []

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
            cohort_symbol = cohort_symbol.upper()
            queryset = Cohort.objects.filter(name_short=cohort_symbol).prefetch_related('sample_set', 'sample_set__sampleset', 'sample_set__score_variants', 'sample_set__score_training')
        except Cohort.DoesNotExist:
            queryset = []
        return queryset


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

class RestGCST(generics.RetrieveAPIView):
    """
    Retrieve all the PGS Score IDs using a given GWAS study (GCST)
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
