from django.http import Http404
from django.shortcuts import render
from django.views.generic import TemplateView
from django.db.models.functions import Lower
import re

from .tables import *


def performance_disclaimer():
    return """<span class="pgs_note_title">Disclaimer: </span>
        The performance metrics are displayed as reported by the source studies.
        It is important to note that metrics are not necessarily comparable with
        each other. For example, metrics depend on the sample characteristics
        (described by the PGS Catalog Sample Set [PSS] ID), phenotyping, and
        statistical modelling. Please refer to the source publication for additional
        guidance on performance."""


def traits_chart_data():
    data = []

    for category in TraitCategory.objects.all().order_by('label'):
        cat_name   = category.label
        cat_colour = category.colour
        cat_scores_count = category.count_scores
        cat_id = category.parent.replace(' ', '_')

        cat_traits = []

        for trait in category.efotraits.order_by(Lower('label')):
            trait_id = trait.id
            trait_name = trait.label
            trait_scores_count = trait.scores_count
            trait_entry = {"name": trait_name, "size": trait_scores_count, "id": trait_id}
            cat_traits.append(trait_entry)

        cat_data = {
          "name": cat_name,
          "colour" : cat_colour,
          "id" : cat_id,
          "size_g": cat_scores_count,
          "children": cat_traits
        }
        data.append(cat_data)

    return data

def index(request):
    current_release = Release.objects.order_by('-date').first()

    context = {
        'release' : current_release,
        'num_pgs' : Score.objects.count(),
        'num_traits' : EFOTrait.objects.count(),
        'num_pubs' : Publication.objects.count(),
        'has_ebi_icons' : 1
    }
    return render(request, 'catalog/index.html', context)

def browseby(request, view_selection):
    context = {}

    if view_selection == 'traits':
        r = Score.objects.all().values('trait_efo').distinct()
        l = []
        for x in r:
            l.append(x['trait_efo'])
        table = Browse_TraitTable(EFOTrait.objects.filter(id__in=l), order_by="label")
        context = {
            'view_name': 'Traits',
            'table': table,
            'data_chart': traits_chart_data(),
            'has_chart': 1
        }
    elif view_selection == 'studies':
        context['view_name'] = 'Publications'
        table = Browse_PublicationTable(Publication.objects.all(), order_by="num")
        context['table'] = table
    elif view_selection == 'sample_set':
        context['view_name'] = 'Sample Sets'
        table = Browse_SampleSetTable(Sample.objects.filter(sampleset__isnull=False))
        context['table'] = table
    else:
        context['view_name'] = 'Polygenic Scores (PGS)'
        table = Browse_ScoreTable(Score.objects.all(), order_by="num")
        context['table'] = table

    context['has_table'] = 1

    return render(request, 'catalog/browseby.html', context)


def pgs(request, pgs_id):
    try:
        score = Score.objects.get(id__exact=pgs_id)
    except Score.DoesNotExist:
        raise Http404("Polygenic Score (PGS): \"{}\" does not exist".format(pgs_id))

    pub = score.publication
    citation = format_html(' '.join([pub.firstauthor, '<i>et al. %s</i>'%pub.journal, '(%s)' % pub.date_publication.strftime('%Y')]))
    citation = format_html('<a target="_blank" href="https://doi.org/{}">{}</a>', pub.doi, citation)
    context = {
        'pgs_id' : pgs_id,
        'score' : score,
        'citation' : citation,
        'performance_disclaimer': performance_disclaimer(),
        'efos' : score.trait_efo.all(),
        'num_variants_pretty' : '{:,}'.format(score.variants_number),
        'has_table': 1
    }

    # Extract and display Sample Tables
    if score.samples_variants.count() > 0:
        table = SampleTable_variants(score.samples_variants.all())
        context['table_sample_variants'] = table
    if score.samples_training.count() > 0:
        table = SampleTable_training(score.samples_training.all())
        context['table_sample_training'] = table

    # Extract + display Performance + associated samples
    pquery = Performance.objects.filter(score=score)
    table = PerformanceTable(pquery)
    context['table_performance'] = table

    pquery_samples = set()
    for q in pquery:
        for sample in q.samples():
            pquery_samples.add(sample)

    table = SampleTable_performance(pquery_samples)
    context['table_performance_samples'] = table

    return render(request, 'catalog/pgs.html', context)


def pgp(request, pub_id):
    try:
        pub = Publication.objects.get(id__exact=pub_id)
    except Publication.DoesNotExist:
        raise Http404("Publication: \"{}\" does not exist".format(pub_id))
    context = {
        'publication' : pub,
        'performance_disclaimer': performance_disclaimer(),
        'has_table': 1
    }

    #Display scores that were developed by this publication
    related_scores = Score.objects.filter(publication=pub)
    if related_scores.count() > 0:
        table = Browse_ScoreTable(related_scores)
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
        context['table_evaluated'] = table

    #Find + table the evaluations
    table = PerformanceTable_PubTrait(pquery)
    context['table_performance'] = table

    pquery_samples = set()
    for q in pquery:
        for sample in q.samples():
            pquery_samples.add(sample)

    table = SampleTable_performance(pquery_samples)
    context['table_performance_samples'] = table

    context['has_table'] = 1
    return render(request, 'catalog/pgp.html', context)


def efo(request, efo_id):
    try:
        trait = EFOTrait.objects.get(id__exact=efo_id)
    except EFOTrait.DoesNotExist:
        raise Http404("Trait: \"{}\" does not exist".format(efo_id))

    related_scores = Score.objects.filter(trait_efo=efo_id)
    context = {
        'trait': trait,
        'performance_disclaimer': performance_disclaimer(),
        'table_scores' : Browse_ScoreTable(related_scores),
        'has_table': 1
    }

    # Check if there are multiple descriptions
    try:
        desc_list = eval(trait.description)
        if type(desc_list) == list:
            context['desc_list'] = desc_list
    except:
        pass

    #Find the evaluations of these scores
    pquery = Performance.objects.filter(score__in=related_scores)
    table = PerformanceTable_PubTrait(pquery)
    context['table_performance'] = table

    pquery_samples = set()
    for q in pquery:
        for sample in q.samples():
            pquery_samples.add(sample)

    table = SampleTable_performance(pquery_samples)
    context['table_performance_samples'] = table

    return render(request, 'catalog/efo.html', context)


def pss(request, pss_id):
    try:
        sample_set = SampleSet.objects.get(id__exact=pss_id)
    except SampleSet.DoesNotExist:
        raise Http404("Sample Set: \"{}\" does not exist".format(pss_id))

    table_cohorts = []
    samples_list = sample_set.samples.all()
    for sample in samples_list:
        # Cohort
        if sample.cohorts.count() > 0:
            table = CohortTable(sample.cohorts.all(), order_by="name_short")
            table_cohorts.append(table)
        else:
            table_cohorts.append('')

    sample_set_data = zip(samples_list, table_cohorts)
    context = {
        'pss_id': pss_id,
        'sample_count': range(len(samples_list)),
        'sample_set_data': sample_set_data,
        'has_table': 1,
        'has_chart': 1
    }
    return render(request, 'catalog/pss.html', context)


class AboutView(TemplateView):
    template_name = "catalog/about.html"

class DocsView(TemplateView):
    template_name = "catalog/docs.html"

class DownloadView(TemplateView):
    template_name = "catalog/download.html"
