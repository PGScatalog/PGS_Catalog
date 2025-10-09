from django.urls import path
from django.views.generic.base import RedirectView
from . import views

urlpatterns = [
    path("validate_metadata/", views.validate_metadata_template_client, name="metadata_template_validation"),
    path("labs/validate_scoring_files/", RedirectView.as_view(pattern_name="scoring_files_validation", permanent=True)),
    path("validate_scoring_files/", views.validate_scoring_files_client, name="scoring_files_validation"),
]