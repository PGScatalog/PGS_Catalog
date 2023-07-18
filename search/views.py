from django.shortcuts import render
from elasticsearch_dsl import Q
from search.documents.efo_trait import EFOTraitDocument
from search.documents.publication import PublicationDocument
from search.documents.score import ScoreDocument
from search.search import EFOTraitSearch, PublicationSearch, ScoreSearch
from django.http import JsonResponse


all_results_scores = {}


def search(request):
    global all_results_scores

    q = request.GET.get('q')
    score_count = 0
    efo_trait_count = 0
    publication_count = 0
    facet_count = 0
    all_results = None
    all_results_scores = {}

    if q:

        # Scores
        score_search = ScoreSearch(q)
        score_results = score_search.search()
        score_count = score_search.count
        format_score_results(request, score_results)

        # EFO Traits
        efo_trait_search = EFOTraitSearch(q)
        efo_trait_results = efo_trait_search.search()
        efo_trait_suggestions = efo_trait_search.suggest()
        efo_trait_count = efo_trait_search.count
        format_efo_traits_results(request, efo_trait_results)

        # Publications
        publication_search = PublicationSearch(q)
        publication_results = publication_search.search()
        publication_count = publication_search.count
        format_publications_results(request, publication_results)

        # Order and structure the results
        if all_results_scores:
            all_results = []
            for score in sorted(all_results_scores, reverse=True):
                for result in all_results_scores[score]:
                    all_results.append(result)

    for facet_result_count in (score_count, efo_trait_count, publication_count):
        if facet_result_count:
            facet_count += 1

    context = {
        'query': q,
        'all_results': all_results,
        'efo_traits_count': efo_trait_count,
        'publications_count': publication_count,
        'scores_count': score_count,
        'facets_count': facet_count,
        'has_table': 1
    }
    return render(request, 'search/search.html', context)


def autocomplete_base(request, query):
    """ Return suggestions for the autocomplete form. """
    max_items = 15
    results = []
    if query:
        # EFO Traits
        efo_trait_search = EFOTraitSearch(query)
        efo_trait_suggestions = efo_trait_search.suggest()

        results = [ result for result in efo_trait_suggestions[:max_items]]

    return JsonResponse({ 'results': results })


def autocomplete(request):
    """ Return suggestions for the autocomplete form. """
    q = request.GET.get('q')

    return autocomplete_base(request,q)

def autocomplete_browse(request):
    """ Return suggestions for the autocomplete form. """
    bq = request.GET.get('bq')

    return autocomplete_base(request,bq)


def format_score_results(request, data):
    """ Convert the Score results into HTML. """
    results = []
    for idx, d in enumerate(data):

        mapped_traits = []
        for trait in d.trait_efo:
            mapped_traits.append(get_efo_trait_url(trait.id, '{} <span class="pgs_bracket">{}</span>'.format(trait.label,trait.id)))

        hmtl_results =  '<div class="pgs_result scores_entry mb-4">'
        hmtl_results += '<div class="pgs_result_title"><h4 class="pgs_facet_icon pgs_facet_1_letter mt-0 mb-2"><a href="/score/{}">{}</a></h4></div>'.format(d.id, d.id)
        hmtl_results += '<div class="pgs_result_content"><b>Name</b>: {}'.format(d.name)
        hmtl_results += '<span><b>Number of Variants</b>: <span class="badge badge-pill badge-pgs">{:,}</span></span>'.format(d.variants_number)
        hmtl_results += '<span><b>Publication ID</b>: {}</span></div>'.format(get_publication_url(d.publication.id, d.publication.id))
        hmtl_results += '<div class="pgs_result_content mt-1"><b>Reported trait</b>: {}'.format( d.trait_reported)
        hmtl_results += '<span><b>Mapped trait(s)</b>: {}</span>'.format(', '.join(mapped_traits))
        hmtl_results += '</div>'
        hmtl_results += '</div>'

        result_score = d.meta.score
        if result_score in all_results_scores:
            all_results_scores[result_score].append(hmtl_results)
        else:
            all_results_scores[result_score] = [hmtl_results]


def format_efo_traits_results(request, data):
    """ Convert the EFO Trait results into HTML. """
    results = []
    for d in data:
        desc = d.description
        if desc:
            desc = desc.replace("['",'').replace("']",'').replace('<','&lt;').replace('>','&gt;')
        else:
            desc = ''
        scores = list(d.scores_direct_associations) + list(d.scores_child_associations)
        scores_count = len(scores)

        categories = '</div><div>'.join([x.label for x in d.traitcategory])

        reported_trait_html = display_reported_traits(d.id, scores)

        hmtl_results =  '<div class="pgs_result efo_traits_entry mb-4">'
        hmtl_results += '  <div class="pgs_result_title">'
        hmtl_results += '    <h4 class="pgs_facet_icon pgs_facet_2_letter mt-0 mb-2 mr-4">{}</h4>'.format(get_efo_trait_url(d.id, d.label))
        hmtl_results += '    <div class="pgs_result_subtitles">'
        hmtl_results += '      <div title="Trait ID">{}</div>'.format(d.id)
        hmtl_results += '      <div title="Trait Category">{}</div>'.format(categories)
        hmtl_results += '    </div>'
        hmtl_results += '  </div>'
        hmtl_results += '  <div class="more">{}</div>'.format(desc)
        hmtl_results += '  <div class="mt-1"><span class="pgs_result_count"><span>Associated PGS</span> <span class="badge badge-pill badge-pgs">{}</span></span> {}</div>'.format(scores_count,reported_trait_html)
        hmtl_results += '</div>'

        result_score = d.meta.score
        if result_score in all_results_scores:
            all_results_scores[result_score].append(hmtl_results)
        else:
            all_results_scores[result_score] = [hmtl_results]


def format_publications_results(request, data):
    """ Convert the Publication results into HTML. """

    results = []
    doi_url = 'https://doi.org/'
    pubmed_url = 'https://www.ncbi.nlm.nih.gov/pubmed/'
    for idx, d in enumerate(data):
        id_suffix =  d.id.replace('PGP','')

        hmtl_results =  '<div class="pgs_result publications_entry mb-4">'
        hmtl_results += '<div class="pgs_result_title"><h4 class="pgs_facet_icon pgs_facet_3_letter mt-0 mb-2">{}</h4></div>'.format(get_publication_url(d.id, d.title))
        hmtl_results += '<div class="pgs_result_content">'
        hmtl_results += '<span>{} et al. ({}) - {}</span>'.format(d.firstauthor, d.pub_year, d.journal)
        if d.PMID:
            hmtl_results += '<span><b>PMID</b>:{}</span>'.format(d.PMID)
        hmtl_results += '<span><b>doi</b>:{}</span>'.format(d.doi)
        hmtl_results += '<span><b>PGP</b>{}</span></div>'.format(id_suffix)
        hmtl_results += '<div class="mt-1"><span class="pgs_result_count">PGS developed <span class="badge badge-pill badge-pgs">{}</span></span> - '.format(d.scores_count);
        hmtl_results += '<span class="pgs_result_count"><span>PGS evaluated</span> <span class="badge badge-pill badge-pgs">{}</span></span></div>'.format(d.scores_evaluated_count)
        hmtl_results += '</div>'

        result_score = d.meta.score
        if result_score in all_results_scores:
            all_results_scores[result_score].append(hmtl_results)
        else:
            all_results_scores[result_score] = [hmtl_results]



def get_efo_trait_url(id,label):
    return f'<a href="/trait/{id}">{label}</a>'

def get_publication_url(id,label):
    return f'<a href="/publication/{id}">{label}</a>'

def get_score_url(id):
    return f'<a href="/score/{id}">{id}</a>'


def display_reported_traits(id,scores):
    """ Build the HTML table listing the reported traits. """

    reported_traits = set()
    for score in scores:
        rt = score.trait_reported
        reported_traits.add(rt)

    reported_trait_html = ''
    for rt in sorted(reported_traits):
        reported_trait_html += '<li>{}</li>'.format(rt)

    score_html =  '<span class="pgs_result_button"> <a class="toggle_btn pgs_btn_plus" id="{}_scores">Show Reported Traits</a></span>'.format(id)
    score_html += '<div class="toggle_content" id="list_{}_scores" style="display:none">'.format(id)
    score_html += '<div class="pgs_result_reported_traits"><ul>{}</ul></div>'.format(reported_trait_html)
    score_html += '</div>'

    return score_html
