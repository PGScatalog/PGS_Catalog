from django.urls import path
from django.views.generic.base import TemplateView

from . import views

urlpatterns = [
    path('labs/benchmarking/', views.benchmark, name='Benchmark')
]
