from django.urls import path, re_path
from django.views.generic import TemplateView
from django.views.decorators.cache import cache_page
from .views import *
from rest_framework.schemas import get_schema_view

# Seconds * Minutes
#cache_time = 60 * 2
cache_time = 0

slash = '/?'
rest_urls = {
    'cohort':         'rest/cohort/',
    'trait':          'rest/trait/',
    'trait_category': 'rest/trait_category/',
    'performance':    'rest/performance/',
    'publication':    'rest/publication/',
    'release':        'rest/release/',
    'sample_set':     'rest/sample_set/',
    'score':          'rest/score/',
    'info':           'rest/info', # No slash (added later)
    'ancestry':       'rest/ancestry_categories', # No slash (added later)
    'gwas':           'rest/gwas/get_score_ids/',
}

urlpatterns = [
    # REST Documentation
    path('rest/', TemplateView.as_view(template_name="rest_api/rest_doc.html")),
    # Cohorts
    re_path(r'^'+rest_urls['cohort']+'all'+slash, cache_page(cache_time)(RestListCohorts.as_view()), name="getAllCohorts"),
    re_path(r'^'+rest_urls['cohort']+'(?P<cohort_symbol>[^/]+)'+slash, RestCohorts.as_view(), name="getCohorts"),
    # EFO Traits
    re_path(r'^'+rest_urls['trait']+'all'+slash, cache_page(cache_time)(RestListEFOTraits.as_view()), name="getAllTraits"),
    re_path(r'^'+rest_urls['trait']+'search'+slash, RestEFOTraitSearch.as_view(), name="searchTraits"),
    re_path(r'^'+rest_urls['trait']+'(?P<trait_id>[^/]+)'+slash, cache_page(cache_time)(RestEFOTrait.as_view()), name="getTrait"),
    # Performance metrics
    re_path(r'^'+rest_urls['performance']+'all'+slash, cache_page(cache_time)(RestListPerformances.as_view()), name="getAllPerformanceMetrics"),
    re_path(r'^'+rest_urls['performance']+'search'+slash, RestPerformanceSearch.as_view(), name="searchPerformanceMetrics"),
    re_path(r'^'+rest_urls['performance']+'(?P<ppm_id>[^/]+)'+slash, RestPerformance.as_view(), name="getPerformanceMetric"),
    # Publications
    re_path(r'^'+rest_urls['publication']+'all'+slash, cache_page(cache_time)(RestListPublications.as_view()), name="getAllPublications"),
    re_path(r'^'+rest_urls['publication']+'search'+slash, cache_page(cache_time)(RestPublicationSearch.as_view()), name="searchPublications"),
    re_path(r'^'+rest_urls['publication']+'(?P<pgp_id>[^/]+)'+slash, RestPublication.as_view(), name="getPublication"),
    # Releases
    re_path(r'^'+rest_urls['release']+'all'+slash, RestListReleases.as_view(), name="getAllReleases"),
    re_path(r'^'+rest_urls['release']+'current'+slash, RestCurrentRelease.as_view(), name="getCurrentRelease"),
    re_path(r'^'+rest_urls['release']+'(?P<release_date>[^/]+)'+slash, RestRelease.as_view(), name="getRelease"),
    # Sample Set
    re_path(r'^'+rest_urls['sample_set']+'all'+slash, cache_page(cache_time)(RestListSampleSets.as_view()), name="getAllSampleSets"),
    re_path(r'^'+rest_urls['sample_set']+'search'+slash, RestSampleSetSearch.as_view(), name="searchSampleSet"),
    re_path(r'^'+rest_urls['sample_set']+'(?P<pss_id>[^/]+)'+slash, RestSampleSet.as_view(), name="getSampleSet"),
    # Scores
    re_path(r'^'+rest_urls['score']+'all'+slash, cache_page(cache_time)(RestListScores.as_view()), name="getAllScores"),
    re_path(r'^'+rest_urls['score']+'search'+slash, RestScoreSearch.as_view(), name="searchScores"),
    re_path(r'^'+rest_urls['score']+'(?P<pgs_id>[^/]+)'+slash, RestScore.as_view(), name="getScore"),
    # Extra endpoints
    re_path(r'^'+rest_urls['gwas']+'(?P<gcst_id>[^/]+)'+slash, cache_page(cache_time)(RestGCST.as_view()), name="pgs_score_ids_from_gwas_gcst_id"),
    re_path(r'^'+rest_urls['info']+slash, cache_page(cache_time)(RestInfo.as_view()), name="getInfo"),
    re_path(r'^'+rest_urls['ancestry']+slash, cache_page(cache_time)(RestAncestryCategories.as_view()), name="getAncestryCategories"),
    # Trait Category
    re_path(r'^'+rest_urls['trait_category']+'all'+slash, cache_page(cache_time)(RestListTraitCategories.as_view()), name="getAllTraitCategories")
]
