from django.urls import path
from . import views

urlpatterns = [
    path('curation_tracker/l1_curation', views.browse_l1_waiting, name='L1 Curation'),
    path('curation_tracker/l2_curation', views.browse_l2_waiting, name='L2 Curation'),
    path('curation_tracker/release_ready', views.browse_release_ready, name='Release Ready'),
    # e.g. /upload/
    path('curation_tracker/stats/', views.stats, name='Curation Stats')
]
