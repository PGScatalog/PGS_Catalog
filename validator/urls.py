from django.urls import path
from . import views

urlpatterns = [
    path("validate_metadata_client/", views.validate_metadata_template_client, name="Metadata Template Validation"),
    path("validate_scoring_files_client/", views.validate_scoring_files_client, name="Scoring Files Validation"),
]