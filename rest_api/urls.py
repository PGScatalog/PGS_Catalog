from django.urls import path
from django.views.generic import TemplateView
from .views import *
from rest_framework.schemas import get_schema_view


urlpatterns = [
    # REST Documentation
    path('rest/', TemplateView.as_view(template_name="rest_api/rest_doc.html")),
    # Cohorts
    path('rest/cohort/<str:cohort_symbol>', RestCohorts.as_view(), name="getCohorts"),
    # EFO Traits
    path('rest/trait/all/', RestListEFOTraits.as_view(), name="getAllTraits"),
    path('rest/trait/<str:trait_id>', RestEFOTrait.as_view(), name="getTrait"),
    path('rest/trait/search/', RestEFOTraitSearch.as_view(), name="searchTraits"),
    # Performance metrics
    path('rest/performance/<str:ppm_id>', RestPerformance.as_view(), name="getPerformanceMetric"),
    path('rest/performance/search/', RestPerformanceSearch.as_view(), name="searchPerformanceMetrics"),
    # Publications
    path('rest/publication/all/', RestListPublications.as_view(), name="getAllPublications"),
    path('rest/publication/<str:pgp_id>', RestPublication.as_view(), name="getPublication"),
    path('rest/publication/search/', RestPublicationSearch.as_view(), name="searchPublications"),
    # Releases
    path('rest/release/all/', RestListReleases.as_view(), name="getAllReleases"),
    path('rest/release/<str:release_date>', RestRelease.as_view(), name="getRelease"),
    path('rest/release/current/', RestCurrentRelease.as_view(), name="getCurrentRelease"),
    # Sample Set
    path('rest/sample_set/<str:pss_id>', RestSampleSet.as_view(), name="getSampleSet"),
    path('rest/sample_set/search/', RestSampleSetSearch.as_view(), name="searchSampleSet"),
    # Scores
    path('rest/score/all/', RestListScores.as_view(), name="getAllScores"),
    path('rest/score/<str:pgs_id>', RestScore.as_view(), name="getScore"),
    path('rest/score/search/', RestScoreSearch.as_view(), name="searchScores"),
    # Extra endpoints
    path('rest/gwas/get_score_ids/<str:gcst_id>', RestGCST.as_view(), name="pgs_score_ids_from_gwas_gcst_id")
]
