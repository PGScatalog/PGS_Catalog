import re, math
from django.http import Http404
from django.shortcuts import render,redirect
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView
from django.db.models import Prefetch
from .models import *
from .tables import *
from catalog.models import Score, EFOTrait
from catalog.views import ancestry_legend

bm_db = 'benchmark'

pgs_prefetch = {
    'trait': Prefetch('trait_efo', queryset=EFOTrait.objects.only('id','label').all()),
}

def benchmark_data(efotrait):

    global bm_db

    chart_data = {
        'cohorts' : [],
        'ancestry_groups': [],
        'pgs_ids': {},
        'ancestries': {},
        'sexes': {},
        'data': {}
    }

    cohort_max_sample = {}

    # Number of decimals to round the estimate
    decimals = 3

    # Performances
    performances = BM_Performance.objects.using(bm_db).select_related('sample','cohort','efotrait').filter(efotrait=efotrait).prefetch_related('performance_metric')

    for performance in performances:
        cohort_name = performance.cohort.name_short
        pgs_id = performance.score_id
        # Sample data
        sample = performance.sample
        sample_number = sample.sample_number
        sample_cases = sample.sample_cases
        sample_cases_percent =  sample.sample_cases_percent
        sample_controls = sample.sample_controls
        ancestry = sample.ancestry_broad
        sex = sample.sample_sex

        # Cohorts
        if not cohort_name in chart_data['cohorts']:
            chart_data['cohorts'].append(cohort_name)

        # Ancestry groups
        if not ancestry in chart_data['ancestry_groups']:
            chart_data['ancestry_groups'].append(ancestry)

        # Sample numbers
        if not cohort_name in cohort_max_sample:
            cohort_max_sample[cohort_name] = {}
        if not ancestry in cohort_max_sample[cohort_name]:
            cohort_max_sample[cohort_name][ancestry] = {}
        if not 'num' in cohort_max_sample[cohort_name][ancestry]:
            cohort_max_sample[cohort_name][ancestry]['num'] = sample_number
        if cohort_max_sample[cohort_name][ancestry]['num'] <= sample_number:
            cohort_max_sample[cohort_name][ancestry]['num'] = sample_number
            cohort_max_sample[cohort_name][ancestry]['display'] = sample.display_samples_for_table(True)

        # PGS IDs
        chart_data = add_global_data(chart_data, cohort_name, pgs_id, 'pgs_ids')

        # Ancestries
        chart_data = add_global_data(chart_data, cohort_name, ancestry, 'ancestries')

        # Sex types
        chart_data = add_global_data(chart_data, cohort_name, sex, 'sexes')

        # Main data (metric)
        if not cohort_name in chart_data['data']:
            chart_data['data'][cohort_name] = {}

        #print(cohort_name+" - "+ancestry+" - "+sex+" - "+pgs_id)

        for metric in performance.performance_metric.all():
            metric_name = metric.name
            estimate = metric.estimate
            ci = metric.ci
            lower_e = upper_e = None
            if ci:
                pattern = re.compile("^\[(.+),\s(.+)\]$")
                m = re.match(pattern,str(ci))
                lower_e = float(m.group(1))
                upper_e = float(m.group(2))

            if not metric_name in chart_data['data'][cohort_name]:
                chart_data['data'][cohort_name][metric_name] = {}
            if not sex in chart_data['data'][cohort_name][metric_name]:
                chart_data['data'][cohort_name][metric_name][sex] = []

            entry = {
                'pgs': pgs_id,
                'anc': ancestry,
                'y': round(estimate, decimals)
            }

            if lower_e and upper_e:
                entry['eb'] = round(lower_e, decimals)
                entry['et'] = round(upper_e, decimals)

            # Sample
            entry['s_num'] = f'{sample_number:,}'
            if sample_cases:
                entry['s_cases'] = f'{sample_cases:,}'
            if sample_cases_percent:
                entry['s_cases_p'] = sample_cases_percent
            if sample_controls:
                entry['s_ctrls'] = f'{sample_controls:,}'

            chart_data['data'][cohort_name][metric_name][sex].append(entry)

    # Sort ancestry_groups
    chart_data['ancestry_groups'] = sort_ancestries(chart_data['ancestry_groups'])

    # Sort each cohort ancestries
    for cohort in chart_data['ancestries']:
        chart_data['ancestries'][cohort] = sort_ancestries(chart_data['ancestries'][cohort])

    # Prepare the data for the Cohort(s) display
    cohort_ancestry_sample = {}
    for cohort in cohort_max_sample:
        if not cohort in cohort_ancestry_sample:
            cohort_ancestry_sample[cohort] = []
            c_ancestries = sort_ancestries(cohort_max_sample[cohort].keys())
            for ancestry in c_ancestries:
                entry = {'name': ancestry, 'display': cohort_max_sample[cohort][ancestry]['display']}
                cohort_ancestry_sample[cohort].append(entry)

    return chart_data, cohort_ancestry_sample


def sort_ancestries(ancestry_list):
    ancestry_list = sorted(ancestry_list)
    eu_ancestry = 'European'
    aa_ancestry = 'African'
    if eu_ancestry in ancestry_list:
        ancestry_list.remove(eu_ancestry)
        ancestry_list.insert(0,eu_ancestry)
    if aa_ancestry in ancestry_list:
        ancestry_list.remove(aa_ancestry)
        ancestry_list.append(aa_ancestry)
    return ancestry_list


def add_global_data(data, cohort_name, entry_name, data_type):
    if not cohort_name in data[data_type]:
        data[data_type][cohort_name] = [entry_name]
    elif not entry_name in data[data_type][cohort_name]:
        data[data_type][cohort_name].append(entry_name)

    return data


def benchmark(request):
    trait_id = 'EFO_0000378'
    efotrait = BM_EFOTrait.objects.using(bm_db).prefetch_related('phenotype_structured').get(id=trait_id)

    pgs_data, cohort_max_sample = benchmark_data(efotrait)

    scores = set()

    cohorts = pgs_data['pgs_ids'].keys()
    for cohort in cohorts:
        for score in pgs_data['pgs_ids'][cohort]:
            scores.add(score)

    score_defer = ['publication__title','publication__PMID','publication__doi','publication__authors','publication__curation_status','publication__curation_notes','publication__date_released','curation_notes']
    table_scores = BM_Browse_ScoreTable(Score.objects.defer(*score_defer).select_related('publication').filter(id__in=list(scores)).prefetch_related(pgs_prefetch['trait']), order_by="num")

    bm_cohorts = BM_Cohort.objects.using(bm_db).filter(name_short__in=cohorts).prefetch_related('cohort_sample').distinct()

    cohort_data = {}
    for bm_cohort in bm_cohorts:
        cohort_name = bm_cohort.name_short
        if not cohort_name in cohort_data:
            ancestry_max_sample = cohort_max_sample[cohort_name]
            cohort_data[cohort_name] = {
                'name': bm_cohort.name_full,
                'ancestries': ancestry_max_sample
            }

    context = {
        'trait': efotrait,
        'pgs_data': pgs_data,
        'table_scores': table_scores,
        'cohorts': cohort_data,
        'ancestry_legend': ancestry_legend(),
        'has_table': 1,
        'has_chart': 1,
        'is_benchmark': 1
    }
    return render(request, 'benchmark/benchmark.html', context)
