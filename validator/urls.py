from django.urls import path
from . import views

urlpatterns = [
    path("validate_metadata/", views.validate_metadata_template_client, name="metadata_template_validation"),
    path("labs/validate_scoring_files/", views.validate_scoring_files_client, name="scoring_files_validation"),
]