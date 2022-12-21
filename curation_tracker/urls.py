from django.urls import path
from django.views.generic.base import TemplateView

from . import views

urlpatterns = [
    path('curation_tracker/l1_curation', views.browse_l1_waiting, name='L1 Curation'),
    path('curation_tracker/l2_curation', views.browse_l2_waiting, name='L2 Curation'),
    path('curation_tracker/release_ready', views.browse_release_ready, name='Release Ready')
]
