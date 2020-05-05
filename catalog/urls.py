from django.urls import path
from django.views.generic.base import TemplateView

from . import views

urlpatterns = [
    path('', views.index, name='index'),

    # ex: /score/PGS000029/
    path('score/<str:pgs_id>/', views.pgs, name='Score'),
    # /!\ Legacy URL /!\ ex: /pgs/PGS000029/
    path('pgs/<str:pgs_id>/', views.redirect_pgs_to_score, name='PGS'),

    # ex: /publication/PGP000001/
    path('publication/<str:pub_id>/', views.pgp, name='Publication'),

    # ex: /trait/EFO_0000305/
    path('trait/<str:efo_id>/', views.efo, name='Polygenic Trait'),

    # ex: /sampleset/PSS000001/
    path('sampleset/<str:pss_id>/', views.pss, name='Sample Set'),

    # ex: /gwas/GCST001937/
    path('gwas/<str:gcst_id>/', views.gwas_gcst, name='NHGRI-EBI GWAS Catalog Study'),

    # ex: /browse/{scores, traits, studies}/
    path('browse/<str:view_selection>/', views.browseby, name='Browse Scores'),

    # ex: /about/
    path('about/', views.AboutView.as_view(), name='About'),

    # ex: /docs/
    path('docs/', views.DocsView.as_view(), name='Documentation'),

    # ex: /downloads/
    path('downloads/', views.DownloadView.as_view(), name='Downloads'),

    #ex: /template/current
    path('template/current', views.CurrentTemplateView.as_view(), name='Current Curation Template'),

    # Setup URL used to warmup the Django app in the Google App Engine
    path('_ah/warmup', views.warmup, name="Warmup"),

    # Setup robots.txt
    path("robots.txt", TemplateView.as_view(template_name="robots.txt", content_type="text/plain"))
]
