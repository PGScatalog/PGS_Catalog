from django.shortcuts import render
from elasticsearch_dsl import Q
from search.documents.efo_trait import EFOTraitDocument
from search.documents.publication import PublicationDocument
from search.documents.score import ScoreDocument
from search.search import EFOTraitSearch, PublicationSearch, ScoreSearch

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
        # EFO Traits
        score_search = ScoreSearch(q)
        score_results = score_search.search()
        score_count = score_search.count
        format_score_results(request, score_results)

        # EFO Traits
        efo_trait_search = EFOTraitSearch(q)
        efo_trait_results = efo_trait_search.search()
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


def format_efo_traits_results(request, data):
    """ Convert the EFO Trait results into HTML. """
    results = []
    icon = '<span class="result_facet_type result_facet_type_1" title="Trait"></span>'
    for d in data:
        desc = d.description
        if desc:
            desc = desc.replace("['",'').replace("']",'')
        else:
            desc = ''


        scores = list(d.scores_direct_associations) + list(d.scores_child_associations)
        score_html =  score_mini_table(d.id, scores)

        categories = '</div><div>'.join([x.label for x in d.traitcategory])

        hmtl_results =  '<div class="pgs_result efo_traits_entry mb-4">'
        hmtl_results += '<div class="pgs_result_title">'
        hmtl_results += '  <h4 class="mt-0 mb-2 mr-4">'
        hmtl_results += '    '+icon+'{}'.format(get_efo_trait_url(d.id, d.label))
        hmtl_results += '  </h4>'
        hmtl_results += '  <div class="pgs_result_subtitles">'
        hmtl_results += '    <div title="Trait ID">{}</div>'.format(d.id)
        hmtl_results += '    <div title="Trait Category">{}</div>'.format(categories)
        hmtl_results += '  </div>'
        hmtl_results += '</div>'
        hmtl_results += '<div class="more">{}</div>'.format(desc)
        hmtl_results += '<div class="mt-1"><span class="pgs_result_count">Associated PGS <span class="badge badge-pill badge-pgs">{}</span></span> {}</div>'.format(len(scores), score_html)
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
    icon = '<span class="result_facet_type result_facet_type_2" title="Publication"></span>'
    for idx, d in enumerate(data):

        score_html =  score_mini_table("pub_"+str(idx), d.publication_score, [x.score for x in d.publication_performance])
        id_suffix =  d.id.replace('PGP','')

        hmtl_results =  '<div class="pgs_result publications_entry mb-4">'
        hmtl_results += '<div class="pgs_result_title"><h4 class="mt-0 mb-2">'+icon+'{}</h4></div>'.format(get_publication_url(d.id, d.title))
        hmtl_results += '<div class="pgs_result_content">{} et al. ({}) - {}'.format(d.firstauthor, d.pub_year, d.journal)
        hmtl_results += '<span><b>PMID</b>:{}</span>'.format( d.PMID)
        hmtl_results += '<span><b>doi</b>:{}</span>'.format(d.doi)
        hmtl_results += '<span><b>PGP</b>{}</span></div>'.format(id_suffix)
        hmtl_results += '<div class="mt-1"><span class="pgs_result_count">PGS developed <span class="badge badge-pill badge-pgs">{}</span></span> - '.format(d.scores_count);
        hmtl_results += '<span class="pgs_result_count">PGS evaluated <span class="badge badge-pill badge-pgs-2">{}</span></span> {}</div>'.format(d.scores_evaluated_count, score_html)
        hmtl_results += '</div>'

        result_score = d.meta.score
        if result_score in all_results_scores:
            all_results_scores[result_score].append(hmtl_results)
        else:
            all_results_scores[result_score] = [hmtl_results]


def format_score_results(request, data):
    """ Convert the Score results into HTML. """
    results = []
    icon = '<span class="result_facet_type result_facet_type_3" title="Score"></span>'
    for idx, d in enumerate(data):

        mapped_traits = []
        for trait in d.trait_efo:
            mapped_traits.append(get_efo_trait_url(trait.id, '{} <span class="pgs_bracket">{}</span>'.format(trait.label,trait.id)))

        hmtl_results =  '<div class="pgs_result scores_entry mb-4">'
        hmtl_results += '<div class="pgs_result_title"><h4 class="mt-0 mb-2">'+icon+'<a href="/score/{}">{}</a></h4></div>'.format(d.id, d.id)
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



def get_efo_trait_url(id,label):
    return f'<a href="/trait/{id}">{label}</a>'

def get_publication_url(id,label):
    return f'<a href="/publication/{id}">{label}</a>'

def get_score_url(id):
    return f'<a href="/score/{id}">{id}</a>'



def score_mini_table(id, scores_developed, scores_evaluated=None):
    """ Build the HTML table listing the Associated PGS. """

    extra_columns = ''
    if scores_evaluated:
        extra_columns = '<th>Developed</th><th>Evaluated</th>'
    score_html =  '<span class="pgs_result_button"> <a class="toggle_btn" id="{}_scores">Show PGS <i class="fa fa-plus-circle"></i></a></span>'.format(id)
    score_html += '<div class="toggle_content" id="list_{}_scores" style="display:none">'.format(id)
    score_html += """<table class="table table-striped table_pgs_score_results mt-2">
        <thead class="thead-light">
            <tr><th>PGS ID</th><th>PGS Name</th><th>Reported Trait</th>"""+extra_columns+"""</tr>
        </thead>
        <tbody>"""

    scores = {}
    for sd in scores_developed:
        score_id = sd.id
        scores[score_id] = { 'score': sd, 'developed': 1, 'evaluated':0 }

    if scores_evaluated:
        for se in scores_evaluated:
            score_id = se.id
            if score_id in scores.keys():
                scores[score_id]['evaluated'] = 1
            else:
                scores[score_id] = { 'score': se, 'developed': 0, 'evaluated': 1 }

    for score in sorted(scores, key=lambda x: scores[x]['score'].trait_reported, reverse=False):
        score_entry = scores[score]['score']
        score_name = score_entry.name
        trait_reported = score_entry.trait_reported

        if scores_evaluated:
            score_dev = '-'
            if scores[score]['developed']:
                score_dev = '<i class="fa fa-check-circle pgs_color_1"></i>'
            score_eval = '-'
            if scores[score]['evaluated']:
                score_eval = '<i class="fa fa-check-circle pgs_color_2"></i>'
            score_html += '<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>'.format(get_score_url(score), score_name, trait_reported, score_dev, score_eval)
        else:
            score_html += '<tr><td>{}</td><td>{}</td><td>{}</td></tr>'.format(get_score_url(score), score_name, trait_reported)
    score_html += '</tbody></table></div>'

    return score_html
