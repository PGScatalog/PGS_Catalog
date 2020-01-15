from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),

    # ex: /pgs/PGS000029/
    path('pgs/<str:pgs_id>/', views.pgs, name='PGS'),

    # ex: /publication/PGP000001/
    path('publication/<str:pub_id>/', views.pgp, name='Publication'),

    # ex: /trait/EFO_0000305/
    path('trait/<str:efo_id>/', views.efo, name='Polygenic Trait'),

    # ex: /sampleset/PSS000001/
    path('sampleset/<str:pss_id>/', views.pss, name='Sample Set'),

    # ex: /browse/{scores, traits, studies}/
    path('browse/<str:view_selection>/', views.browseby, name='Browse Scores'),

    # ex: /about/
    path('about/', views.AboutView.as_view(), name='About'),

    # ex: /docs/
    path('docs/', views.DocsView.as_view(), name='Documentation'),

    # ex: /downloads/
    path('downloads/', views.DownloadView.as_view(), name='Downloads')
]
