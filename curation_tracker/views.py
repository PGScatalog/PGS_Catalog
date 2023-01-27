import os
from django.http import Http404
from django.shortcuts import render
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView
from django.conf import settings
from django.db.models import Prefetch

from pgs_web import constants
from .tables import *


curation_tracker = 'curation_tracker'
l1_curation_done = ['Curation done','Curation done (AS)']
not_awaiting_curation = [*l1_curation_done,'Determined ineligible']

# Create your views here.

def browse_l1_waiting(request):
    l1_waiting = CurationPublicationAnnotation.objects.using(curation_tracker).exclude(first_level_date__isnull=True,second_level_date__isnull=True).exclude(first_level_curation_status__in=not_awaiting_curation)
    table_l1 = Browse_CurationPublicationAnnotationL1(l1_waiting)
    context = {
        'table': table_l1,
        'has_table': 1
    }
    return render(request, 'curation_tracker/l1_curation.html', context)

def browse_l2_waiting(request):
    l2_waiting = CurationPublicationAnnotation.objects.using(curation_tracker).filter(first_level_date__isnull=False,first_level_curation_status__in=l1_curation_done,second_level_date__isnull=True).exclude(second_level_curation_status=not_awaiting_curation)
    table_l2 = Browse_CurationPublicationAnnotationL2(l2_waiting)
    context = {
      'table': table_l2,
      'has_table': 1
    }
    return render(request, 'curation_tracker/l2_curation.html', context)


def browse_release_ready(request):
    context = {}
    import_ready_count = CurationPublicationAnnotation.objects.using(curation_tracker).filter(curation_status='Curated - Awaiting Import').count()
    context['studies_to_import_count'] = import_ready_count
    if import_ready_count:
        import_ready = CurationPublicationAnnotation.objects.using(curation_tracker).filter(curation_status='Curated - Awaiting Import')
        context['table_to_import'] = Browse_CurationPublicationAnnotationReleaseReady(import_ready)

    release_ready_count = CurationPublicationAnnotation.objects.using(curation_tracker).filter(curation_status='Imported - Awaiting Release').count()
    context['studies_to_release_count'] = release_ready_count
    if release_ready_count:
        release_ready = CurationPublicationAnnotation.objects.using(curation_tracker).filter(curation_status='Imported - Awaiting Release')
        context['table_to_release'] = Browse_CurationPublicationAnnotationReleaseReady(release_ready)

    if context:
        context['has_table'] = 1
    return render(request, 'curation_tracker/release_ready.html', context)
