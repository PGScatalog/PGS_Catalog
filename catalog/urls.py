from django.urls import path
from django.views.generic.base import RedirectView, TemplateView
from django.views.decorators.cache import cache_page

from . import views

# Seconds * Minutes
cache_time = 60 * 60

urlpatterns = [
    path('', cache_page(cache_time)(views.index), name='index'),

    # e.g.: /score/PGS000029/
    path('score/<str:pgs_id>/', views.pgs, name='Score'),
    # /!\ Legacy URL /!\ ex: /pgs/PGS000029/
    path('pgs/<str:pgs_id>/', views.redirect_pgs_to_score, name='PGS'),

    # e.g.: /publication/PGP000001/
    path('publication/<str:pub_id>/', views.pgp, name='Publication'),

    # e.g.: /trait/EFO_0000305/
    path('trait/<str:efo_id>/', views.efo, name='Polygenic Trait'),

    # e.g.: /sampleset/PSS000001/
    path('sampleset/<str:pss_id>/', views.pss, name='Sample Set'),

    # e.g.: /gwas/GCST001937/
    path('gwas/<str:gcst_id>/', views.gwas_gcst, name='NHGRI-EBI GWAS Catalog Study'),

    # e.g.: /browse/{scores, traits, studies, sample_set}/
    path('browse/<str:view_selection>/', cache_page(cache_time)(views.browseby), name='Browse data'),

    # e.g.: /latest_release/
    path('latest_release/', cache_page(cache_time)(views.latest_release), name='Latest Release'),

    # e.g.: /news/
    # path('news/', views.NewsView.as_view(), name='News'),

    # e.g.: /about/
    path('about/', views.AboutView.as_view(), name='About'),

    # e.g.: /docs/ancestry/
    path('docs/ancestry/', views.ancestry_doc, name='Ancestry'),

    # e.g.: /docs/
    path('docs/', views.DocsView.as_view(), name='Documentation'),

    # e.g.: /docs/faq/
    path('docs/faq/', views.FaqDocsView.as_view(), name='Frequently Asked Questions'),

    # e.g.: /downloads/
    path('downloads/', views.DownloadView.as_view(), name='Downloads'),

    # e.g.: /submit/
    path('submit/', RedirectView.as_view(url='/about/#submission')),

    # e.g.: /report_study/
    path('report_study/', views.ReportStudyView.as_view(), name='Report missing PGS study'),

    # e.g.: /template/current
    path('template/current', views.CurrentTemplateView.as_view(), name='Current Curation Template'),

    # e.g.: /docs/curation
    path('docs/curation', views.CurationDocView.as_view(), name='Curation documentation'),

    # e.g.: /labs
    path('labs/', views.LabsView.as_view(), name="Labs"),

    # Setup URL used to warmup the Django app in the Google App Engine
    path('_ah/warmup', views.warmup, name="Warmup"),

    # Setup robots.txt
    path("robots.txt", TemplateView.as_view(template_name="robots.txt", content_type="text/plain"))
]
