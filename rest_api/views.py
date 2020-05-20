from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.views import exception_handler
from rest_framework.exceptions import Throttled
from django.db.models import Prefetch
from catalog.models import *
from .serializers import *

generic_defer = ['curation_notes','date_released']
related_dict = {
    'score_prefetch' : [Prefetch('trait_efo', queryset=EFOTrait.objects.defer('synonyms','mapped_terms').all()), 'samples_variants', 'samples_variants__cohorts', 'samples_variants__sample_age', 'samples_variants__followup_time', 'samples_training', 'samples_training__cohorts', 'samples_training__sample_age', 'samples_training__followup_time'],
    'perf_select': ['score', 'publication', 'sampleset'],
    'publication_score_prefetch': [Prefetch('publication_score', queryset=Score.objects.only('id','publication__id').all())],
    'score_set_prefetch': [Prefetch('score_set', queryset=Score.objects.only('id','trait_efo__id').all())],
    'score_defer': [*generic_defer,'publication__curation_status','publication__curation_notes','publication__date_released','publication__authors'],
    'perf_defer': [*generic_defer,'score__curation_notes','score__date_released','publication__curation_status','publication__curation_notes','publication__date_released','publication__authors'],
    'publication_defer': [*generic_defer,'curation_status']
}

def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    if isinstance(exc, Throttled): # check that a Throttled exception is raised
        response.data = { # custom response data
            'message': 'request limit exceeded',
            'availableIn': '%d seconds'%exc.wait
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
    queryset = Publication.objects.defer(*related_dict['publication_defer']).all().prefetch_related(*related_dict['publication_score_prefetch']).order_by('num')
    serializer_class = PublicationExtendedSerializer


class RestPublication(APIView):
    """
    Retrieve one PGS Publication
    """

    def get(self, request, pgp_id):
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


class RestScore(APIView):
    """
    Retrieve one PGS Score
    """

    def get(self, request, pgs_id):
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
            queryset = queryset.filter(trait_efo__id=trait_id)
            params += 1

        if params == 0:
            queryset = []

        return queryset


## Performance metrics ##

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
            try:
                queryset = queryset.filter(score__id=pgs_id)
            except Score.DoesNotExist:
                queryset = []
        else:
            queryset = []

        return queryset


class RestPerformance(APIView):
    """
    Retrieve one Performance metric
    """

    def get(self, request, ppm_id):
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
    queryset = EFOTrait.objects.all().prefetch_related(*related_dict['score_set_prefetch']).order_by('label')
    serializer_class = EFOTraitExtendedSerializer


class RestEFOTrait(APIView):
    """
    Retrieve one EFO Trait
    """

    def get(self, request, trait_id):
        trait_id = trait_id.replace(':', '_')
        try:
            queryset = EFOTrait.objects.prefetch_related(*related_dict['score_set_prefetch']).get(id=trait_id)
        except EFOTrait.DoesNotExist:
            queryset = None
        serializer = EFOTraitExtendedSerializer(queryset,many=False)
        return Response(serializer.data)


class RestEFOTraitSearch(generics.ListAPIView):
    """
    Retrieve the EFO Trait(s) using query
    """
    serializer_class = EFOTraitExtendedSerializer

    def get_queryset(self):

        queryset = EFOTrait.objects.all().prefetch_related(*related_dict['score_set_prefetch']).order_by('label')

        # Search by trait term
        term = self.request.query_params.get('term')
        if term and term is not None:
            queryset = queryset.filter(label__icontains=term) | queryset.filter(synonyms__icontains=term) | queryset.filter(mapped_terms__icontains=term)
        else:
            queryset = []
        return queryset


## Samples / Sample Sets ##

class RestSampleSet(APIView):
    """
    Retrieve one Sample Set
    """

    def get(self, request, pss_id):
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


class RestRelease(APIView):
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


class RestCurrentRelease(APIView):
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
    Retrieve all the PGS Score IDs using a given GWAS study (GCST)
    """

    def get(self, request, gcst_id):
        samples = Sample.objects.filter(source_GWAS_catalog=gcst_id).distinct()

        try:
            scores = Score.objects.only('id').filter(samples_variants__in=samples).distinct()
        except Score.DoesNotExist:
            scores = []

        pgs_scores = [score.id for score in scores]

        return Response(pgs_scores)
