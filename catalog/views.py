from django.http import Http404
from django.shortcuts import render
from django.views.generic import TemplateView

from django_tables2 import RequestConfig
from .tables import *

def index(request):
    context = {
        'num_pgs' : Score.objects.count(),
        'num_traits' : EFOTrait.objects.count(),
        'num_pubs' : Publication.objects.count()
    }
    return render(request, 'catalog/index.html', context)

def browseby(request, view_selection):
    context = {}

    if view_selection == 'traits':
        context['view_name'] = 'Polygenic Traits'
        r = Score.objects.all().values('trait_efo').distinct()
        l = []
        for x in r:
            l.append(x['trait_efo'])
        table = Browse_TraitTable(EFOTrait.objects.filter(id__in=l))
        RequestConfig(request, paginate={"per_page": 100}).configure(table)
        context['table'] = table
    elif view_selection == 'studies':
        context['view_name'] = 'Publications'
        table = Browse_PublicationTable(Publication.objects.all())
        RequestConfig(request, paginate={"per_page": 100}).configure(table)
        context['table'] = table
    else:
        context['view_name'] = 'Polygenic Scores'
        table = Browse_ScoreTable(Score.objects.all())
        RequestConfig(request, paginate={"per_page": 100}).configure(table)
        context['table'] = table

    return render(request, 'catalog/browseby.html', context)

def pgs(request, pgs_id):
    try:
        score = Score.objects.get(id__exact=pgs_id)
    except Score.DoesNotExist:
        raise Http404("Polygenic Score (PGS): \"{}\" does not exist".format(pgs_id))

    pub = score.publication
    citation = format_html(' '.join([pub.firstauthor, '<i>et al. %s</i>'%pub.journal, '(%s)' % pub.date_publication.strftime('%Y')]))
    citation = format_html('<a href=../../publication/{}>{}</a>', pub.id, citation)
    context = {
        'pgs_id' : pgs_id,
        'score' : score,
        'citation' : citation,
        'efos' : score.trait_efo.all(),
        'num_variants_pretty' : '{:,}'.format(score.variants_number)
    }

    # Extract and display Sample Tables
    if score.samples_variants.count() > 0:
        table = SampleTable_variants(score.samples_variants.all())
        RequestConfig(request).configure(table)
        context['table_sample_variants'] = table
    if score.samples_training.count() > 0:
        table = SampleTable_training(score.samples_training.all())
        RequestConfig(request).configure(table)
        context['table_sample_training'] = table

    # Extract + display Performance + associated samples
    pquery = Performance.objects.filter(score=score)
    table = PerformanceTable(pquery)
    RequestConfig(request).configure(table)
    context['table_performance'] = table

    pquery_samples = []
    for q in pquery:
        pquery_samples = pquery_samples + q.samples()

    table = SampleTable_performance(pquery_samples)
    RequestConfig(request).configure(table)
    context['table_performance_samples'] = table

    return render(request, 'catalog/pgs.html', context)

def pgp(request, pub_id):
    try:
        pub = Publication.objects.get(id__exact=pub_id)
    except Publication.DoesNotExist:
        raise Http404("Publication: \"{}\" does not exist".format(pub_id))
    context = {
        'publication': pub
    }

    #Display scores that were developed by this publication
    related_scores = Score.objects.filter(publication=pub)
    if related_scores.count() > 0:
        table = Browse_ScoreTable(related_scores)
        RequestConfig(request).configure(table)
        context['table_scores'] = table

    #Get PGS evaluated by the PGP
    pquery = Performance.objects.filter(publication=pub)

    # Check if there any of the PGS are externally developed + display their information
    external_scores = set()
    for perf in pquery:
        if perf.score not in related_scores:
            external_scores.add(perf.score)
    if len(external_scores) > 0:
        table = Browse_ScoreTable(external_scores)
        RequestConfig(request).configure(table)
        context['table_evaluated'] = table

    #Find + table the evaluations
    table = PerformanceTable_PubTrait(pquery)
    RequestConfig(request).configure(table)
    context['table_performance'] = table

    pquery_samples = []
    for q in pquery:
        pquery_samples = pquery_samples + q.samples()

    table = SampleTable_performance(pquery_samples)
    RequestConfig(request).configure(table)
    context['table_performance_samples'] = table

    return render(request, 'catalog/pgp.html', context)

def efo(request, efo_id):
    try:
        trait = EFOTrait.objects.get(id__exact=efo_id)
    except EFOTrait.DoesNotExist:
        raise Http404("Trait: \"{}\" does not exist".format(efo_id))

    related_scores = Score.objects.filter(trait_efo=efo_id)
    context = {
        'trait': trait,
        'table_scores' : Browse_ScoreTable(related_scores)
    }

    #Check if there are multiple descriptions
    try:
        desc_list = eval(trait.description)
        if type(desc_list) == list:
            context['desc_list'] = desc_list
    except:
        pass

    #Find the evaluations of these scores
    pquery = Performance.objects.filter(score__in=related_scores)
    table = PerformanceTable_PubTrait(pquery)
    RequestConfig(request).configure(table)
    context['table_performance'] =table

    pquery_samples = []
    for q in pquery:
        pquery_samples = pquery_samples + q.samples()

    table = SampleTable_performance(pquery_samples)
    RequestConfig(request).configure(table)
    context['table_performance_samples'] = table

    return render(request, 'catalog/efo.html', context)

class DocsView(TemplateView):
    template_name = "catalog/docs.html"

class DownloadView(TemplateView):
    template_name = "catalog/download.html"
