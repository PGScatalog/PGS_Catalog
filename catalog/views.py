import os
from django.http import Http404
from django.shortcuts import render,redirect
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView
from django.conf import settings
from django.db.models import Prefetch

from pgs_web import constants
from .tables import *


generic_attributes =['publication__title','publication__PMID','publication__doi','publication__authors','publication__curation_status','publication__curation_notes','publication__date_released']
pgs_only = {
    'publication_performance': ['id','score_id','sampleset_id','publication_id','phenotyping_reported','covariates','performance_comments','score__id','score__name','score__publication_id','publication__id','publication__journal','publication__date_publication','publication__firstauthor']
}
pgs_defer = {
    'generic_with_curation': generic_attributes,
    'generic': [*generic_attributes, 'curation_notes'],
    'perf'   : [*generic_attributes,'date_released','score__curation_notes','score__date_released'],
    'perf_extra': ['score__method_name','score__method_params','score__variants_interactions','score__ancestries','score__license'],
    'publication_sel': ['publication__title','publication__authors','publication__curation_notes','publication__curation_status','publication__date_released'],
    'publication_no_curation': ['curation_status','curation_notes'],
    'sample': ['sample_age','followup_time','source_GWAS_catalog','source_DOI','source_PMID','ancestry_country']
}
pgs_prefetch = {
    'cohorts': Prefetch('cohorts', queryset=Cohort.objects.only('name_short','name_full').all()),
    'trait': Prefetch('trait_efo', queryset=EFOTrait.objects.only('id','label').all().order_by('id')),
    'publication': Prefetch('publication', queryset=Publication.objects.only('id','date_publication','journal','firstauthor').all()),
    'publication_score': Prefetch('publication_score', queryset=Score.objects.only('id', 'publication').all()),
    'publication_score_2': Prefetch('publication_score', queryset=Score.objects.only('id','name','trait_reported','variants_number','ancestries','license','publication').all()),
    'publication_performance': Prefetch('publication_performance', queryset=Performance.objects.only('id', 'score','publication').all().prefetch_related(Prefetch('score', queryset=Score.objects.only('id', 'publication').all()))),
    'publication_performance_2': Prefetch('publication_performance', queryset=Performance.objects.only('id', 'score','publication').all().prefetch_related(Prefetch('score', queryset=Score.objects.only('id', 'name').all()))),
    'sampleset__samples': Prefetch('sampleset__samples', queryset=Sample.objects.select_related('sample_age','followup_time').all().prefetch_related('sampleset','cohorts')),
    'score__publication': Prefetch('score__publication', queryset=Publication.objects.only('id','date_publication','firstauthor','journal').all())
}
performance_prefetch = [pgs_prefetch['score__publication'], pgs_prefetch['sampleset__samples'], 'phenotyping_efo', 'performance_metric']


def disclaimer_formatting(func):
    def wrapper(*args):
        return f'<div class="clearfix"><div class="mt-2 float_left pgs_note pgs_note_2"><div><span>Disclaimer: </span>{func(*args)}</div></div></div>'
    return wrapper

@disclaimer_formatting
def performance_disclaimer():
    return constants.DISCLAIMERS['performance']

@disclaimer_formatting
def score_disclaimer(publication_url):
    return constants.DISCLAIMERS['score'].format(publication_url)


def ancestry_legend():
    ''' HTML code for the Ancestry legend. '''
    ancestry_labels = constants.ANCESTRY_LABELS
    count = 0;
    ancestry_keys = ancestry_labels.keys()
    val = len(ancestry_keys) / 2
    entry_per_col = int((len(ancestry_keys) + 1) / 2);

    div_html_1 = '<div class="ancestry_legend'

    div_html = div_html_1

    legend_html = ''
    div_content = ''
    for key in ancestry_keys:
        if count == entry_per_col:
            div_html += ' mr-3">'
            div_html += div_content+'</div>'
            legend_html += div_html
            # New div
            div_html = div_html_1
            div_content = ''
            count = 0

        label = ancestry_labels[key]
        div_content += '<div><span class="ancestry_box_legend anc_colour_'+key+'" data-key="'+key+'"></span>'+label+'</div>'
        count += 1
    div_html += '">'+div_content+'</div>'
    legend_html += div_html

    return '''
    <div id="ancestry_legend" class="filter_container mb-3">
        <div class="filter_header">Ancestry legend <a class="pgs_no_icon_link info-icon" target="_blank" href="/docs/ancestry/#anc_category" data-toggle="tooltip" data-placement="bottom" title="Click on this icon to see more information about the Ancestry Categories (open in a new tab)"><i class="fas fa-info-circle"></i></a></div>
        <div id="ancestry_legend_content">{}</div>
    </div>'''.format(legend_html)


def ancestry_form():
    ''' HTML code for the Ancestry form. '''

    option_html = ''

    ancestry_labels = constants.ANCESTRY_LABELS
    for key in ancestry_labels.keys():

        label = ancestry_labels[key]

        if key != 'MAO' and key != 'MAE':
          opt = f'<option value="{key}">{label}</option>'
          option_html += opt

    checkbox_title_eur = 'This button can be used to hide PGS with any European ancestry data to only show scores with data from other non-European ancestry group. The button is selected by default, displaying all PGS.'
    checkbox_title_multi = 'Shows only PGS that include data from multiple ancestry groups at the selected study stage, hiding PGS with data from a single ancestry group.'

    return '''
    <div class="mb-3 pgs_form_container">
        <!-- Ancestry form -->
        <div id="ancestry_filter" class="filter_container mr-3 mb-3">
            <div class="filter_header">Filter PGS by Participant Ancestry <a class="pgs_no_icon_link info-icon" target="_blank" href="/docs/ancestry/#anc_filter" data-toggle="tooltip" data-placement="bottom" title="Click on this icon to see information about the Ancestry Filters (open in a new tab)"><i class="fas fa-info-circle"></i></a></div>
            <div class="filter_form">
              <!-- Type of study -->
              <div class="filter_study">
                <div class="filter_subheader mb-1">Individuals included in:</div>
                  <select id="ancestry_type_list">
                    <option value="all" selected>All Stages combined [G, D, E]</option>
                    <option value="dev_all">Development [G, D]</option>
                    <option value="gwas">&nbsp;&nbsp;- GWAS [G]</option>
                    <option value="dev">&nbsp;&nbsp;- Score development [D]</option>
                    <option value="eval">PGS Evaluation [E]</option>
                  </select>
                  <div class="ancestry_legend pl-1 mt-2">
                    <div><b>G</b> - Source of Variant Associations (<b>G</b>WAS)</div>
                    <div><b>D</b> - Score <b>D</b>evelopment/Training</div>
                    <div><b>E</b> - PGS <b>E</b>valuation</div>
                  </div>
                </div>
                <!-- Type of ancestry -->
                <div class="filter_ancestry">
                <div id="single_ancestry" class="filter_subheader mb-1">List of ancestries includes:</div>
                  <div>
                    <select id="ancestry_filter_ind">
                      <option value="">--</option>
                      {ancestry_option}
                    </select>
                  </div>
                  <div class="filter_subheader mt-2">Display options:</div>
                  <div id="ancestry_filter_list">
                    <div class="custom-control custom-switch">
                      <input type="checkbox" class="custom-control-input ancestry_filter_cb" value="" data-default="true" id="anc_cb_EUR" checked>
                      <label class="custom-control-label" for="anc_cb_EUR">Show European ancestry data</label><span class="info-icon-small" data-toggle="tooltip" data-placement="right" title="{title_eur}"><i class="fas fa-info-circle"></i></span>
                    </div>
                    <div class="custom-control custom-switch">
                      <input type="checkbox" class="custom-control-input ancestry_filter_cb" value="MAO" data-default="false" id="anc_cb_multi">
                      <label class="custom-control-label" for="anc_cb_multi">Show <u>only</u> Multi-ancestry data</label><span class="info-icon-small" data-toggle="tooltip" data-placement="right" title="{title_multi}"><i class="fas fa-info-circle"></i></span>
                    </div>
                  </div>
                </div>
            </div>
        </div>
        {ancestry_legend}
    </div>'''.format(ancestry_option=option_html, ancestry_legend=ancestry_legend(), title_eur=checkbox_title_eur, title_multi=checkbox_title_multi)


def get_efo_traits_data():
    """ Generate the list of traits and trait categories in PGS."""
    data = []
    # Use set() to avoid duplication when an entry belongs to several categories
    traits_list = set()
    for category in TraitCategory.objects.all().prefetch_related('efotraits__associated_scores','efotraits__traitcategory').order_by('label'):
        cat_scores_count = 0
        cat_id = category.parent.replace(' ', '_')

        cat_traits = []

        for trait in category.efotraits.all():
            trait_scores_count = trait.scores_count
            if trait_scores_count == 0:
                continue
            cat_scores_count += trait_scores_count
            trait_entry = {
                "name": trait.label,
                "size": trait_scores_count,
                "id": trait.id
            }
            cat_traits.append(trait_entry)
            # Traits table
            traits_list.add(trait)

        if cat_scores_count == 0:
            continue

        cat_traits.sort(key=lambda x: x["name"].lower())

        cat_data = {
          "name": category.label,
          "colour" : category.colour,
          "id" : cat_id,
          "size_g": cat_scores_count,
          "children": cat_traits
        }
        data.append(cat_data)

    traits_list = list(traits_list)
    traits_list.sort(key=lambda x: x.label)

    return [traits_list, data]


def format_model_numbers(models_count):
    return f'{models_count:,}'


def index(request):
    current_release = Release.objects.values('date','score_count','publication_count').order_by('-date').first()

    scores_count = Score.objects.count()
    traits_count = EFOTrait.objects.count()
    pubs_count = Publication.objects.count()

    context = {
        'release' : current_release,
        'num_pgs' : format_model_numbers(scores_count),
        'num_traits' : format_model_numbers(traits_count),
        'num_pubs' : format_model_numbers(pubs_count),
        'has_ebi_icons' : 1,
        'is_homepage': 1
    }

    if hasattr(constants, 'ANNOUNCEMENT'):
        if constants.ANNOUNCEMENT and constants.ANNOUNCEMENT != '':
            context['announcement'] = constants.ANNOUNCEMENT

    # Count non-released Entries
    if settings.PGS_ON_CURATION_SITE:
        released_traits = set()
        for score in Score.objects.only('num').filter(date_released__isnull=False).prefetch_related('trait_efo'):
            for efo in score.trait_efo.all():
                released_traits.add(efo.id)
        released_traits_count = len(list(released_traits))
        trait_diff = traits_count - released_traits_count
        if trait_diff != 0:
            context['num_traits_not_released'] = trait_diff
        context['num_pgs_not_released']  = Score.objects.filter(date_released__isnull=True).count()
        context['num_pubs_not_released'] = Publication.objects.filter(date_released__isnull=True).count()

    return render(request, 'catalog/index.html', context)


def browseby(request, view_selection):
    context = {}

    if view_selection == 'traits':
        efo_traits_data = get_efo_traits_data()
        table = Browse_TraitTable(efo_traits_data[0])
        context = {
            'view_name': 'Traits',
            'table': table,
            'data_chart': efo_traits_data[1],
            'has_ebi_icons': 1,
            'has_chart': 1
        }
    elif view_selection == 'studies':
        publication_defer = ['authors','curation_status','curation_notes','date_released']
        publication_prefetch_related = [pgs_prefetch['publication_score'], pgs_prefetch['publication_performance']]
        publications = Publication.objects.defer(*publication_defer).all().prefetch_related(*publication_prefetch_related)
        table = Browse_PublicationTable(publications, order_by="num")
        context = {
            'view_name': 'Publications',
            'has_ebi_icons': 1,
            'table': table
        }
    elif view_selection == 'pending_studies':
        publication_defer = ['authors','curation_notes','date_released']
        publication_prefetch_related = [pgs_prefetch['publication_score'], pgs_prefetch['publication_performance']]
        pending_publications = Publication.objects.defer(*publication_defer).filter(date_released__isnull=True).prefetch_related(*publication_prefetch_related)
        table = Browse_PendingPublicationTable(pending_publications, order_by="num")
        context = {
            'view_name': 'Pending Publications',
            'table': table
        }
    # elif view_selection == 'sample_set':
    #     context['view_name'] = 'Sample Sets'
    #     table = Browse_SampleSetTable(Sample.objects.defer(*pgs_defer['sample']).filter(sampleset__isnull=False).prefetch_related('sampleset', pgs_prefetch['cohorts']).order_by('sampleset__num'))
    #     context['table'] = table
    elif view_selection == 'scores' :
        score_only_attributes = ['id','name','trait_efo','trait_reported','variants_number','ancestries','license','publication__id','publication__date_publication','publication__journal','publication__firstauthor']
        table = Browse_ScoreTable(Score.objects.only(*score_only_attributes).select_related('publication').all().order_by('num').prefetch_related(pgs_prefetch['trait']))
        context = {
            'view_name': 'Polygenic Scores (PGS)',
            'table': table,
            'ancestry_form': ancestry_form(),
            'has_chart': 1
        }
    elif view_selection == 'all':
        return redirect('/browse/scores/', permanent=True)
    else:
        return redirect('/', permanent=True)

    context['has_table'] = 1

    return render(request, 'catalog/browseby.html', context)


def latest_release(request):

    context = {
        'ancestry_form': ancestry_form(),
        'release_date': 'NA',
        'publications_count': 0,
        'scores_count': 0,
        'has_table': 1,
        'has_chart': 1
    }

    latest_release = Release.objects.values('date','score_count','publication_count').order_by('-date').first()
    if latest_release:
        release_date = latest_release['date']

        context['release_date'] = release_date

        # Publications
        publication_defer = ['authors','curation_status','curation_notes']
        publication_prefetch_related = [pgs_prefetch['publication_score'], pgs_prefetch['publication_performance']]
        publications = Publication.objects.defer(*publication_defer).filter(date_released=release_date).prefetch_related(*publication_prefetch_related)
        publications_table = Browse_PublicationTable(publications, order_by="num")
        context['publications_table'] = publications_table
        context['publications_count'] = latest_release['publication_count']

        # Scores
        score_only_attributes = ['id','name','trait_efo','trait_reported','variants_number','ancestries','license','publication__id','publication__date_publication','publication__journal','publication__firstauthor']
        scores_table = Browse_ScoreTable(Score.objects.only(*score_only_attributes,'date_released').select_related('publication').filter(date_released=release_date).order_by('num').prefetch_related(pgs_prefetch['trait']))
        context['scores_table'] = scores_table
        context['scores_count'] = latest_release['score_count']

    return render(request, 'catalog/latest_release.html', context)


def pgs(request, pgs_id):
    # If ID in lower case, redirect with the ID in upper case
    if not pgs_id.isupper():
        return redirect_with_upper_case_id(request, '/score/', pgs_id)

    template_html_file = 'pgs.html'

    try:
        prefetch_related_score = ['trait_efo','samples_variants','samples_training','samples_variants__cohorts','samples_training__cohorts']
        if settings.PGS_ON_CURATION_SITE == 'True':
            score = Score.objects.defer(*pgs_defer['generic_with_curation']).select_related('publication').prefetch_related(*prefetch_related_score).get(id__exact=pgs_id)
        else:
            score = Score.objects.defer(*pgs_defer['generic']).select_related('publication').prefetch_related(*prefetch_related_score).get(id__exact=pgs_id)

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
            'has_table': 1,
            'has_chart': 1
        }
        if not score.flag_asis:
            context['score_disclaimer'] = score_disclaimer(score.publication.doi)

        # Extract and display Sample Tables
        if score.samples_variants.count() > 0:
            table = SampleTable_variants(score.samples_variants.all())
            context['table_sample_variants'] = table
        if score.samples_training.count() > 0:
            table = SampleTable_training(score.samples_training.all())
            context['table_sample_training'] = table

        # Extract + display Performance + associated samples
        pquery = Performance.objects.defer(*pgs_defer['perf'],*pgs_defer['perf_extra'],*pgs_defer['publication_sel']).select_related('score','publication').filter(score=score).prefetch_related(*performance_prefetch)
        table = PerformanceTable(pquery)
        table.exclude = ('score')
        context['table_performance'] = table

        pquery_samples = set()
        for q in pquery:
            for sample in q.samples():
                pquery_samples.add(sample)

        table = SampleTable_performance(pquery_samples)
        context['table_performance_samples'] = table

    except Score.DoesNotExist:
        try:
            embargoed_score = EmbargoedScore.objects.get(id=pgs_id)
            embargoed_pub = EmbargoedPublication.objects.get(firstauthor=embargoed_score.firstauthor)
            template_html_file = 'embargoed/'+template_html_file
            context = { 'score' : embargoed_score, 'publication': embargoed_pub }
        except EmbargoedScore.DoesNotExist:
            try:
                retired_score = Retired.objects.get(id=pgs_id)
                template_html_file = 'retired/'+template_html_file
                context = { 'score' : retired_score }
            except Retired.DoesNotExist:
                raise Http404("Polygenic Score (PGS): \"{}\" does not exist".format(pgs_id))

    return render(request, 'catalog/'+template_html_file, context)


def redirect_with_upper_case_id(request, dir, id):
    id = id.upper()
    response = redirect(dir+str(id), permanent=True)
    return response


def redirect_pgs_to_score(request, pgs_id):
    response = redirect_with_upper_case_id(request, '/score/', pgs_id)
    return response


def pgp(request, pub_id):
    # If ID in lower case, redirect with the ID in upper case
    if not pub_id.isupper():
        return redirect_with_upper_case_id(request, '/publication/', pub_id)

    template_html_file = 'pgp.html'
    try:
        if settings.PGS_ON_CURATION_SITE:
            pub = Publication.objects.prefetch_related(pgs_prefetch['publication_score_2'], 'publication_performance').get(id__exact=pub_id)
        else:
            pub = Publication.objects.defer(*pgs_defer['publication_no_curation']).prefetch_related(pgs_prefetch['publication_score_2'], 'publication_performance').get(id__exact=pub_id)

        context = {
            'publication' : pub,
            'performance_disclaimer': performance_disclaimer(),
            'has_table': 1,
            'has_chart': 1,
            'has_ebi_icons': 1,
            'ancestry_form': ancestry_form()
        }

        # Display scores that were developed by this publication
        related_scores = pub.publication_score.defer(*pgs_defer['generic']).select_related('publication').all().prefetch_related(pgs_prefetch['trait'])
        if related_scores.count() > 0:
            table = Browse_ScoreTable(related_scores)
            context['table_scores'] = table

        # Get PGS evaluated by the PGP
        count_perf = pub.publication_performance.all().count()
        external_scores = set()

        # Very large study
        if count_perf >= constants.TABLE_ROWS_THRESHOLD:
            context['perf_count'] = count_perf

            # Get externally developped scores
            external_scores = set()
            score_ids = pub.publication_evaluatedscore.values_list('scores_evaluated__id', flat=True).all()
            score_only_cols = ['id','name','trait_reported','variants_number','ancestries','license']
            pub_only_cols = ['publication__id','publication__journal','publication__date_publication','publication__firstauthor']
            scores = Score.objects.only(*score_only_cols,*pub_only_cols).select_related('publication').filter(id__in=score_ids).prefetch_related(pgs_prefetch['trait'])
            # Check if there any of the PGS are externally developed
            for score in scores:
                if score not in related_scores:
                    external_scores.add(score)
        # Other study
        else:
            extra_score_cols = ['score__trait_reported','score__variants_number','score__ancestries','score__license']
            pquery = pub.publication_performance.only(*pgs_only['publication_performance'],*extra_score_cols).select_related('score','publication').all().prefetch_related(*performance_prefetch, 'score__trait_efo')

            pquery_samples = set()

            for perf in pquery:
                # Check if there any of the PGS are externally developed
                perf_score = perf.score
                if perf_score not in related_scores:
                    external_scores.add(perf_score)

                # Fetch Samples from SampleSets
                for sample in perf.samples():
                    pquery_samples.add(sample)

            # Performance table
            table = PerformanceTable(pquery)
            context['table_performance'] = table

            # SampleSet table
            table = SampleTable_performance(pquery_samples)
            context['table_performance_samples'] = table

        # External Scores Evaluated By This Publication
        if len(external_scores) > 0:
            table = Browse_ScoreTableEval(external_scores)
            context['table_evaluated'] = table

        context['has_table'] = 1

    except Publication.DoesNotExist:
        try:
            embargoed_pub = EmbargoedPublication.objects.get(id=pub_id)
            embargoed_scores = EmbargoedScore.objects.filter(firstauthor=embargoed_pub.firstauthor).order_by('id')
            table = EmbargoedScoreTable(embargoed_scores)
            embargoed_scores_count = EmbargoedScore.objects.filter(firstauthor=embargoed_pub.firstauthor).count()
            template_html_file = 'embargoed/'+template_html_file
            context = { 'publication' : embargoed_pub, 'scores_count': embargoed_scores_count, 'scores_table': table, 'has_table': 1}
        except EmbargoedPublication.DoesNotExist:
            try:
                retired_publication = Retired.objects.get(id=pub_id)
                template_html_file = 'retired/'+template_html_file
                context = { 'publication' : retired_publication }
            except Retired.DoesNotExist:
                raise Http404("Publication: \"{}\" does not exist".format(pub_id))

    return render(request, 'catalog/'+template_html_file, context)


def efo(request, efo_id):
    # Check for redirection (different case/separator for the ID)
    special_source_replacement = False
    special_source_found = False
    separator_change = False
    url_dir = '/trait/'
    # If ID with ':', redirect using the ID with '_'
    if ':' in efo_id:
        efo_id = efo_id.replace(':','_')
        separator_change = True
    efo_id_lc = efo_id.lower()
    # Check if the trait ID belongs to a source where the prefix is not in upper case (e.g. Orphanet)
    for source in constants.TRAIT_SOURCE_TO_REPLACE:
        source_lc = source.lower()
        if efo_id.startswith(source):
            special_source_found = True
            break
        elif efo_id_lc.startswith(source_lc):
            efo_id = efo_id_lc.replace(source_lc,source)
            special_source_found = True
            special_source_replacement = True
            break
    # If ID in lower case, redirect with the ID in upper case
    # Exception for certain trait sources (e.g. Orphanet)
    if special_source_found:
        if special_source_replacement or separator_change:
            return redirect(url_dir+efo_id, permanent=True)
    elif not efo_id.isupper() or separator_change:
        return redirect_with_upper_case_id(request, url_dir, efo_id)

    exclude_children = False
    include_children = request.GET.get('include_children');
    if include_children:
        if include_children.lower() == 'false':
            exclude_children = True

    try:
        ontology_trait = EFOTrait_Ontology.objects.prefetch_related('scores_direct_associations','scores_child_associations','child_traits','traitcategory').get(id__exact=efo_id)
    except EFOTrait_Ontology.DoesNotExist:
        raise Http404("Trait: \"{}\" does not exist".format(efo_id))

    # Get list of PGS Scores
    related_direct_scores = ontology_trait.scores_direct_associations.defer(*pgs_defer['generic']).select_related('publication').all().prefetch_related(pgs_prefetch['trait'])
    related_child_scores = ontology_trait.scores_child_associations.defer(*pgs_defer['generic']).select_related('publication').all().prefetch_related(pgs_prefetch['trait'])
    if exclude_children:
        related_scores = related_direct_scores
    else:
        merged_related_scores = list(related_direct_scores) + list(related_child_scores)
        # Remove potential duplicates (e.g. one of the trait is also a child of the second trait)
        related_scores = list(set(merged_related_scores))
        related_scores.sort(key=lambda x: x.id)

    context = {
        'trait': ontology_trait,
        'trait_id_with_colon': ontology_trait.id.replace('_', ':'),
        'trait_scores_direct_count': len(related_direct_scores),
        'trait_scores_child_count': len(related_child_scores),
        'performance_disclaimer': performance_disclaimer(),
        'table_scores': Browse_ScoreTable(related_scores),
        'include_children': False if exclude_children else True,
        'has_table': 1,
        'has_chart': 1,
        'has_ebi_icons': 1,
        'ancestry_form': ancestry_form()
    }

    # Find the evaluations of these scores
    pquery = Performance.objects.defer(*pgs_defer['perf'],*pgs_defer['publication_sel']).select_related('score','publication').filter(score__in=related_scores).prefetch_related(*performance_prefetch)

    table = PerformanceTable(pquery)
    context['table_performance'] = table

    pquery_samples = set()
    for q in pquery:
        for sample in q.samples():
            pquery_samples.add(sample)

    table = SampleTable_performance(pquery_samples)
    context['table_performance_samples'] = table

    return render(request, 'catalog/efo.html', context)


def gwas_gcst(request, gcst_id):
    # If ID in lower case, redirect with the ID in upper case
    if not gcst_id.isupper():
        return redirect_with_upper_case_id(request, '/gwas/', gcst_id)

    samples = Sample.objects.filter(source_GWAS_catalog__exact=gcst_id).distinct()
    if len(samples) == 0:
        raise Http404("No PGS Samples are associated with the NHGRI-GWAS Catalog Study: \"{}\"".format(gcst_id))

    related_scores = Score.objects.defer(*pgs_defer['generic']).select_related('publication').filter(samples_variants__in=samples).prefetch_related(pgs_prefetch['trait']).distinct()
    if len(related_scores) == 0:
        raise Http404("No PGS Scores are associated with the NHGRI-GWAS Catalog Study: \"{}\"".format(gcst_id))

    context = {
        'gwas_id': gcst_id,
        'performance_disclaimer': performance_disclaimer(),
        'table_scores' : Browse_ScoreTable(related_scores),
        'has_table': 1,
        'use_gwas_api': 1,
        'ancestry_form': ancestry_form(),
        'has_chart': 1
    }

    pquery = Performance.objects.defer(*pgs_defer['perf'],*pgs_defer['publication_sel']).select_related('score','publication').filter(score__in=related_scores).prefetch_related(*performance_prefetch)
    table = PerformanceTable(pquery)
    context['table_performance'] = table

    pquery_samples = set()
    for q in pquery:
        for sample in q.samples():
            pquery_samples.add(sample)

    table = SampleTable_performance(pquery_samples)
    context['table_performance_samples'] = table

    return render(request, 'catalog/gwas_gcst.html', context)


def pss(request, pss_id):
    # If ID in lower case, redirect with the ID in upper case
    if not pss_id.isupper():
        return redirect_with_upper_case_id(request, '/sampleset/', pss_id)

    try:
        sample_set = SampleSet.objects.prefetch_related('samples', 'samples__cohorts', 'samples__sample_age', 'samples__followup_time').get(id__exact=pss_id)
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

    related_performance = Performance.objects.only(*pgs_only['publication_performance']).select_related('score','publication').filter(sampleset=sample_set).prefetch_related(pgs_prefetch['score__publication'], 'score__trait_efo', 'sampleset', 'phenotyping_efo', 'performance_metric')
    if related_performance.count() > 0:
        # Scores
        related_scores = [x.score for x in related_performance]
        table_scores = Browse_ScoreTable(related_scores)
        context['table_scores'] = table_scores
        # Display performance metrics associated with this sample set
        table_performance = PerformanceTable(related_performance)
        table_performance.exclude = ('sampleset')
        context['table_performance'] = table_performance
        context['performance_disclaimer'] = performance_disclaimer()

    return render(request, 'catalog/pss.html', context)


def ancestry_doc(request):
    pgs_id = "PGS000018"
    try:
        score = Score.objects.defer(*pgs_defer['generic']).select_related('publication').prefetch_related('trait_efo').get(id=pgs_id)
        table_score = Browse_ScoreTableExample([score])
        context = {
            'pgs_id_example': pgs_id,
            'ancestry_legend': ancestry_legend(),
            'table_score': table_score,
            'has_table': 1,
            'has_chart': 1
        }
    except:
        context = {}
    return render(request, 'catalog/docs/ancestry.html', context)


def releases(request):

    release_data = []
    pub_per_year_data = { 'all': [] }

    total_score = 0
    total_perf = 0
    total_publi = 0
    max_score = 0
    max_publi = 0
    max_perf = 0
    max_width = 100

    ## Publications distribution
    # All publications
    pub_per_year = {}
    publications = Publication.objects.all()
    for publication in publications:
        year = publication.pub_year
        if year in pub_per_year:
            pub_per_year[year] += 1
        else:
            pub_per_year[year] = 1

    for p_year in sorted(pub_per_year.keys()):
        pub_per_year_item = { 'year': p_year, 'count': pub_per_year[p_year] }
        pub_per_year_data['all'].append(pub_per_year_item)

    # Separate the "Released" and "Not released" Publications
    nr_publications = Publication.objects.filter(date_released__isnull=True)
    if len(nr_publications) > 0:
        nr_pub_per_year = {}
        for nr_publication in nr_publications:
            year = nr_publication.pub_year
            if year in nr_pub_per_year:
                nr_pub_per_year[year] += 1
            else:
                nr_pub_per_year[year] = 1
        pub_per_year_data['nr'] = []
        for p_year in sorted(nr_pub_per_year.keys()):
            pub_per_year_item = { 'year': p_year, 'count': nr_pub_per_year[p_year] }
            pub_per_year_data['nr'].append(pub_per_year_item)

        r_publications = Publication.objects.exclude(date_released__isnull=True)
        if len(r_publications) > 0:
            r_pub_per_year = {}
            for r_publication in r_publications:
                year = r_publication.pub_year

                if year in r_pub_per_year:
                    r_pub_per_year[year] += 1
                else:
                    r_pub_per_year[year] = 1
            pub_per_year_data['r'] = []
            for p_year in sorted(r_pub_per_year.keys()):
                pub_per_year_item = { 'year': p_year, 'count': r_pub_per_year[p_year] }
                pub_per_year_data['r'].append(pub_per_year_item)

    # Get max data
    releases_list = Release.objects.order_by('date')
    for release in releases_list:
        score = release.score_count
        perf  = release.performance_count
        publi = release.publication_count
        if score > max_score:
            max_score = score
        if publi > max_publi:
            max_publi = publi
        if perf > max_perf:
            max_perf = perf

    for release in releases_list:
        score = release.score_count
        perf  = release.performance_count
        publi = release.publication_count
        date  = release.date

        release_item = {
                        'date': date.strftime('%d/%m/%y'),
                        'score_count': score,
                        'performance_count': perf,
                        'publication_count': publi,
                        'total_score_count': total_score,
                        'total_performance_count': total_perf,
                        'total_publication_count': total_publi
                       }
        total_score += score
        total_perf += perf
        total_publi += publi

        release_data.append(release_item)

    ordered_releases_list = list(releases_list.order_by('-date'))

    context = {
        'latest_release': ordered_releases_list.pop(0),
        'previous_releases_list': ordered_releases_list,
        'releases_data': release_data,
        'pub_per_year_data': pub_per_year_data,
        'max_score': max_score,
        'max_publi': max_publi,
        'max_perf': max_perf,
        'has_table': 1,
        'has_chart_js': 1,
        'use_release_charts': 1

    }
    return render(request, 'catalog/releases.html', context)


def stats(request):
    # Variant numbers
    variants_number_list = Score.objects.values_list('variants_number', flat=True).all()
    variants_number_per_score = round(sum(variants_number_list) / len(variants_number_list))

    # Global Counts
    publications_count = Publication.objects.count()
    scores_count = Score.objects.count()
    performances_count = Performance.objects.count()

    # Studies per score
    eval_scores_pubs = Performance.objects.values_list('score_id','publication_id').distinct()

    colours = TraitCategory.objects.values_list('colour', flat=True).all().order_by('colour')

    # Genome builds
    genomebuild_data = get_data_distribution('variants_genomebuild',scores_count,colours)

    # Weight types
    weight_type_data = get_data_distribution('weight_type',scores_count,colours,1)

    # Methods
    method_data = get_data_distribution('method_name',scores_count,colours)

    # Reported traits
    reported_trait_data = get_data_distribution('trait_reported',scores_count,colours)

    context = {
        'variants_number_per_score': '{:,}'.format(variants_number_per_score),
        'scores_per_pub': round(scores_count/publications_count,1),
        'pub_eval_per_score': round(len(eval_scores_pubs)/scores_count,1),
        'evals_per_score': round(performances_count/scores_count,1),
        'genomebuild_data': genomebuild_data,
        'weight_type_data': weight_type_data,
        'method_data': method_data,
        'reported_trait_data': reported_trait_data,
        'has_chart': 1
    }
    return render(request, 'catalog/docs/stats.html', context)


def get_data_distribution(model_attribute,scores_count,colours,use_others=None):
    items = Score.objects.values_list(model_attribute, flat=True).all()
    tmp_data = {}
    for item in items:
        if item in tmp_data.keys():
            tmp_data[item] += 1
        else:
            tmp_data[item] = 1
    data_list = []
    data_others_list = []
    index = 0
    for label in tmp_data.keys():
        # Group minor entry (e.g. with only 1 occurence)
        if use_others and tmp_data[label] == 1:
            data_others_list.append({ 'name': label, 'count': '{:,}'.format(tmp_data[label]) })
        else:
            percent = round((tmp_data[label]/scores_count)*100,2)
            data_list.append(
                { 'name': label, 'value': percent, 'count': '{:,}'.format(tmp_data[label]), 'colour': colours[index] }
            )
            index += 1
        if index == len(colours):
            index = 0
    data_list = sorted(data_list, key=lambda d: d['name'].lower())
    # Build the "Others" row
    if use_others and data_others_list:
        label_id = 'stats_others_'+model_attribute
        label = '<a class="toggle_btn pgs_btn_plus" id="'+label_id+'" title="Click to expand/collapse the list">Others ('+str(len(data_others_list))+')</a>'
        label += '<div class="toggle_list" id="list_'+label_id+'"><ul>'
        for other_entry in sorted(data_others_list, key=lambda d: d['name'].lower()):
            label += f"<li>{other_entry['name']}: {other_entry['count']}</li>"
        label += '</ul></div>'
        data_list.append(
            { 'name': label, 'value': percent, 'count': '{:,}'.format(len(data_others_list)), 'colour': colours[index] }
        )
    return data_list


class NewsView(TemplateView):
    template_name = "catalog/news.html"

class AboutView(TemplateView):
    template_name = "catalog/docs/about.html"

class DocsView(TemplateView):
    template_name = "catalog/docs/docs.html"

class FaqDocsView(TemplateView):
    template_name = "catalog/docs/faq.html"

class DownloadView(TemplateView):
    template_name = "catalog/download.html"

class ReportStudyView(TemplateView):
    template_name = "catalog/report_study.html"

class LabsView(TemplateView):
    template_name = "catalog/labs.html"

class CurrentTemplateView(RedirectView):
    url = constants.USEFUL_URLS['TEMPLATEGoogleDoc_URL']

class CurationDocView(RedirectView):
    url = constants.USEFUL_URLS['CurationGoogleDoc_URL']


# Method used for the App Engine warmup
def warmup(request):
    """
    Provides default procedure for handling warmup requests on App
    Engine. Just add this view to your main urls.py.
    """
    import importlib
    from django.http import HttpResponse
    for app in settings.INSTALLED_APPS:
        for name in ('urls', 'views', 'models'):
            try:
                importlib.import_module('%s.%s' % (app, name))
            except ImportError:
                pass
    content_type = 'text/plain; charset=utf-8'
    return HttpResponse("Warmup done.", content_type=content_type)
