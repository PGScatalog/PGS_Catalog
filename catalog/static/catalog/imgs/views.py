from django.http import Http404
from django.shortcuts import render
from django.views.generic import TemplateView
import re

#from django_tables2 import RequestConfig
from .tables import *

def charts(request):

    # Scores per trait
    scores_per_trait = {}
    efo_per_trait = {}
    for trait in EFOTrait.objects.all():
        label = trait.label
        scores_per_trait[label] = trait.scores_count
        efo_per_trait[label] = trait.id

    traits_list = []
    efo_list = []
    score_counts_list = []
    score_counts_category = {}
    for trait, count in sorted(scores_per_trait.items()):
        efo_list.append(efo_per_trait[trait])
        traits_list.append(trait+" ("+str(count)+")")
        score_counts_list.append(count)

        if re.search("cancer", trait) or re.search("carcinoma", trait):
            if "cancer" in score_counts_category:
                score_counts_category["cancer"] = score_counts_category["cancer"] + count
            else:
                score_counts_category["cancer"] = count
        elif re.search("diabetes", trait):
            if "diabetes" in score_counts_category:
                score_counts_category["diabetes"] = score_counts_category["diabetes"] + count
            else:
                score_counts_category["diabetes"] = count
        elif re.search("heart", trait) or re.search("artery", trait) or re.search("fibrillation", trait):
            if "heart disease" in score_counts_category:
                score_counts_category["heart disease"] = score_counts_category["heart disease"] + count
            else:
                score_counts_category["heart disease"] = count
        else:
            score_counts_category[trait] = count

    colours_list = get_colours_list(len(traits_list))

    colours_list_cat = get_colours_list(len(score_counts_category.keys()))

    index = 0
    colours_legend = []
    for trait in traits_list:
        tuple = (trait,efo_list[index],colours_list[index])
        colours_legend.append(tuple)
        index = index + 1

    index = 0
    colours_legend_cat = []
    traits_list_cat = []
    counts_per_category = []
    for cat in sorted(score_counts_category.keys()):
        tuple = (cat,colours_list_cat[index])
        colours_legend_cat.append(tuple)
        traits_list_cat.append(cat)
        counts_per_category.append(score_counts_category[cat])
        index = index + 1

    # Variants per PGS
    variants_per_score_cat = {}
    for score in Score.objects.all():
        variants = str(score.variants_number);
        unit_size = len(variants)
        upper_unit = "1"
        for i in range(0,unit_size):
            upper_unit = upper_unit + '0'
        if upper_unit in variants_per_score_cat:
            variants_per_score_cat[upper_unit] = variants_per_score_cat[upper_unit] + 1
        else:
            variants_per_score_cat[upper_unit] = 1

    var_colours_list = get_colours_list(len(variants_per_score_cat.keys()))

    counts_per_var_cat = []
    var_cat_list = []
    for var_cat in sorted(variants_per_score_cat.keys()):
        var_cat_formatted = format(int(var_cat), ",")
        var_cat_list.append("Under "+var_cat_formatted+" variants ("+str(variants_per_score_cat[var_cat])+")")
        counts_per_var_cat.append(variants_per_score_cat[var_cat])

    context = {
        'scores_per_trait'    : [traits_list,score_counts_list,efo_list,colours_list,colours_legend],
        'scores_per_category' : [traits_list_cat,counts_per_category,colours_list_cat,colours_legend_cat],
        'var_per_pgs'         : [var_cat_list,counts_per_var_cat,var_colours_list]
    }
    return render(request, 'catalog/charts.html', context)


def random_colours():
    r = random.randint(0,255)
    g = random.randint(0,255)
    b = random.randint(0,255)
    return "rgb(" + str(r) + "," + str(g) + "," + str(b) + ")";

def get_colours_list(number):
    colours_list = ['rgb(230, 25, 75)', 'rgb(60, 180, 75)', 'rgb(255, 225, 25)', 'rgb(0, 130, 200)', 'rgb(245, 130, 48)', 'rgb(145, 30, 180)', 'rgb(70, 240, 240)', 'rgb(240, 50, 230)', 'rgb(210, 245, 60)', 'rgb(250, 190, 190)', 'rgb(0, 128, 128)', 'rgb(230, 190, 255)', 'rgb(170, 110, 40)', 'rgb(255, 250, 200)', 'rgb(128, 0, 0)', 'rgb(170, 255, 195)', 'rgb(128, 128, 0)', 'rgb(255, 215, 180)', 'rgb(0, 0, 128)', 'rgb(128, 128, 128)']
    number_of_colours_to_add = number - len(colours_list)
    if (number_of_colours_to_add > 0):
        for c in range(0,number):
            colour = random_colours()
            if colour in colours_list:
                loop_max = 0
                while colour in colours_list or loop_max<10:
                    colour = random_colours()
                loop_max = 0
            colours_list.append(colour)

    return colours_list

def get_lighter_colour(rgb_colour):
    """ Generate a slightly lighter colour/tint from the RGB provided """
    tint_factor = 0.9
    currentRGB = re.match(r"rgb\((\d+)\,\s?(\d+)\,\s?(\d+)",rgb_colour)
    newRGB = []
    for i in range(1,4):
        currentC = currentRGB.group(i)
        newC = round(255 - (255 - int(currentC)) * tint_factor)
        print("> "+str(currentC)+" | "+str(newC))
        if (newC > 255):
            newC = 255
        newRGB.append(str(newC))
    return "rgb("+', '.join(newRGB)+")"


def traits_chart_data():
    data = [
        {
          "name": "Nervous system disease",
          "colour" : "rgb(230, 25, 75)",
          "id" : "nervous",
          "size_g": 2,
          "children": [
            {"name": "Alzheimer's disease", "size": 2}
          ]
        },
        {
          "name": "Body weights and measures",
          "colour" : "rgb(60, 180, 75)",
          "id" : "body",
          "size_g": 2,
          "children": [
            {"name": "body mass index", "size": 2}
          ]
        },
        {
          "name": "Cancer",
          "colour" : "rgb(255, 225, 25)",
          "id" : "cancer",
          "size_g": 13,
          "children": [
            {"name": "breast carcinoma", "size": 6},
            {"name": "estrogen-receptor negative breast cancer", "size": 3},
            {"name": "estrogen-receptor positive breast cancer", "size": 3},
            {"name": "prostate carcinoma", "size": 1}
          ]
        },
        {
          "name": "Cardiovascular disease",
          "colour" : "rgb(245, 130, 48)",
          "id" : "cardio",
          "size_g": 8,
          "children": [
            {"name": "atrial fibrillation", "size": 2},
            {"name": "coronary artery disease", "size": 5},
            {"name": "coronary heart disease", "size": 1}
          ]
        },
        {
          "name": "Metabolic disease",
          "colour" : "rgb(0, 130, 200)",
          "id" : "metabo",
          "size_g": 10,
          "children": [
            {"name": "type I diabetes mellitus", "size": 4},
            {"name": "type II diabetes mellitus", "size": 6}
          ]
        },
        {
          "name": "Inflammatory bowel disease",
          "colour" : "rgb(145, 30, 180)",
          "id" : "ibd",
          "size_g": 1,
          "children": [
            {"name": "inflammatory bowel disease", "size": 1}
          ]
        }
      ]

    return data

####################################################

def index(request):
    #current_release = Release.objects.filter(is_current=1).last()
    current_release = Release.objects.order_by('-date').first()

    context = {
        'release' : current_release,
        'num_pgs' : Score.objects.count(),
        'num_traits' : EFOTrait.objects.count(),
        'num_pubs' : Publication.objects.count()
    }
    return render(request, 'catalog/index.html', context)

def browseby(request, view_selection):
    context = {}

    if view_selection == 'traits':
        context['view_name'] = 'Traits'
        r = Score.objects.all().values('trait_efo').distinct()
        l = []
        for x in r:
            l.append(x['trait_efo'])
        table = Browse_TraitTable(EFOTrait.objects.filter(id__in=l), order_by="label")
        #RequestConfig(request, paginate={"per_page": 100}).configure(table)
        context['table'] = table
        context['data_chart'] = traits_chart_data()
    elif view_selection == 'studies':
        context['view_name'] = 'Publications'
        table = Browse_PublicationTable(Publication.objects.all())
        #RequestConfig(request, paginate={"per_page": 100}).configure(table)
        context['table'] = table
    elif view_selection == 'sample_set':
        context['view_name'] = 'Sample Sets'
        table = Browse_SampleSetTable(Sample.objects.filter(sampleset__isnull=False))
        #RequestConfig(request, paginate={"per_page": 100}).configure(table)
        context['table'] = table
    else:
        context['view_name'] = 'Polygenic Scores'
        table = Browse_ScoreTable(Score.objects.all())
        #RequestConfig(request, paginate={"per_page": 100}).configure(table)
        context['table'] = table

    return render(request, 'catalog/browseby.html', context)

def pgs(request, pgs_id):
    try:
        score = Score.objects.get(id__exact=pgs_id)
    except Score.DoesNotExist:
        raise Http404("Polygenic Score (PGS): \"{}\" does not exist".format(pgs_id))

    pub = score.publication
    citation = format_html(' '.join([pub.firstauthor, '<i>et al. %s</i>'%pub.journal, '(%s)' % pub.date_publication.strftime('%Y')]))
    citation = format_html('<a target="_blank" href=https://doi.org/{}>{}</a>', pub.doi, citation)
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
        #RequestConfig(request).configure(table)
        context['table_sample_variants'] = table
    if score.samples_training.count() > 0:
        table = SampleTable_training(score.samples_training.all())
        #RequestConfig(request).configure(table)
        context['table_sample_training'] = table

    # Extract + display Performance + associated samples
    pquery = Performance.objects.filter(score=score)
    table = PerformanceTable(pquery)
    #RequestConfig(request).configure(table)
    context['table_performance'] = table

    pquery_samples = []
    for q in pquery:
        pquery_samples = pquery_samples + q.samples()

    table = SampleTable_performance(pquery_samples)
    #RequestConfig(request).configure(table)
    context['table_performance_samples'] = table

    return render(request, 'catalog/pgs.html', context)

def pgp(request, pub_id):
    try:
        pub = Publication.objects.get(id__exact=pub_id)
    except Publication.DoesNotExist:
        raise Http404("Publication: \"{}\" does not exist".format(pub_id))
    context = {
        'publication' : pub
    }

    #Display scores that were developed by this publication
    related_scores = Score.objects.filter(publication=pub)
    if related_scores.count() > 0:
        table = Browse_ScoreTable(related_scores)
        #RequestConfig(request).configure(table)
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
        #RequestConfig(request).configure(table)
        context['table_evaluated'] = table

    #Find + table the evaluations
    table = PerformanceTable_PubTrait(pquery)
    #RequestConfig(request).configure(table)
    context['table_performance'] = table

    pquery_samples = []
    for q in pquery:
        pquery_samples = pquery_samples + q.samples()

    table = SampleTable_performance(pquery_samples)
    #RequestConfig(request).configure(table)
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
    #RequestConfig(request).configure(table)
    context['table_performance'] =table

    pquery_samples = []
    for q in pquery:
        pquery_samples = pquery_samples + q.samples()

    table = SampleTable_performance(pquery_samples)
    #RequestConfig(request).configure(table)
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
            #RequestConfig(request).configure(table)
            table_cohorts.append(table)
        else:
            table_cohorts.append('')

    sample_set_data = zip(samples_list, table_cohorts)
    context = {
        'pss_id': pss_id,
        'sample_count': range(len(samples_list)),
        'sample_set_data': sample_set_data
    }
    return render(request, 'catalog/pss.html', context)

def releases(request):
    releases_list = Release.objects.order_by('-date')
    context = {
        'releases_list': releases_list
    }
    return render(request, 'catalog/releases.html', context)

class AboutView(TemplateView):
    template_name = "catalog/about.html"

class DocsView(TemplateView):
    template_name = "catalog/docs.html"

class DownloadView(TemplateView):
    template_name = "catalog/download.html"
