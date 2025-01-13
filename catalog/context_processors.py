from django.conf import settings
from pgs_web import constants

def pgs_settings(request):
    return {
        'is_pgs_app_on_gae' : settings.PGS_ON_GAE,
        'is_pgs_live_site' : settings.PGS_ON_LIVE_SITE,
        'is_pgs_curation_site': settings.PGS_ON_CURATION_SITE
    }

def pgs_urls(request):
    return {
        'nhgri_url'        : constants.USEFUL_URLS['NHGRI_URL'],
        'baker_url'        : constants.USEFUL_URLS['BAKER_URL'],
        'ebi_url'          : constants.USEFUL_URLS['EBI_URL'],
        'hdr_uk_cam_url'   : constants.USEFUL_URLS['HDR_UK_CAM_URL'],
        'pgs_contact'      : constants.USEFUL_URLS['PGS_CONTACT'],
        'pgs_ftp_root'     : constants.USEFUL_URLS['PGS_FTP_ROOT'],
        'pgs_ftp_http_root': constants.USEFUL_URLS['PGS_FTP_HTTP_ROOT'],
        'pgs_ftp_http_meta': constants.USEFUL_URLS['PGS_FTP_HTTP_ROOT']+'/metadata/',
        'pgs_github'       : constants.USEFUL_URLS['PGS_GITHUB'],
        'pgs_twitter'      : constants.USEFUL_URLS['PGS_TWITTER'],
        'pgs_twitter_url'  : constants.USEFUL_URLS['PGS_TWITTER_URL'],
        'pgs_bluesky': constants.USEFUL_URLS['PGS_BLUESKY'],
        'pgs_bluesky_url': constants.USEFUL_URLS['PGS_BLUESKY_URL'],
        'uoc_url'          : constants.USEFUL_URLS['UOC_URL'],
        'terms_of_use'     : constants.USEFUL_URLS['TERMS_OF_USE'],
        'catalog_publication_url': constants.USEFUL_URLS['CATALOG_PUBLICATION_URL']
    }

def pgs_search_examples(request):
    eg_count = 0
    html = ''
    # Build the list of search examples
    for example in constants.SEARCH_EXAMPLES:
        link = f'<a href="/search?q={example}">{example}</a>'
        eg_count += 1
        if eg_count > 1:
            if eg_count == 4:
                html += '<span class="extra_example">'
            html += ', '
        html += link
    if eg_count > 3:
        html += '</span>'
    return {
        'pgs_search_examples': html
    }

def pgs_info(request):
    return {
        'pgs_citation': constants.PGS_CITATIONS[0],
        'pgs_citations': constants.PGS_CITATIONS,
        'pgs_publications': constants.PGS_PUBLICATIONS,
        'pgs_table_helper': constants.TABLE_HELPER,
        'ensembl_version': constants.ENSEMBL_VERSION
    }

def pgs_contributors(request):
    groups = constants.PGS_GROUPS
    groups_to_print = list()
    html='<p><b>PGS Catalog Team:</b> '

    def get_group_index(group_private_index):
        group = groups.get(group_private_index, None)
        group_name = group['name']
        if not group in groups_to_print:
            groups_to_print.append(group)
        group_index = groups_to_print.index(group) + 1
        return(f'<a title="{group_name}" style="border-bottom: 0px;">{group_index}</a>')
    
    def html_author(author):
        name = author['name']
        group_sup = ','.join(map(get_group_index,author['group']))
        
        return f'<span>{ name }<sup>{ group_sup }</sup></span>'

    html += ', '.join(map(html_author,constants.PGS_CONTRIBUTORS))
    html += '</p>\n'
    html += '<p><b>Previous Contributors:</b>\n'
    html += ', '.join(map(html_author,constants.PGS_PREVIOUS_CONTRIBUTORS))

    html += '</p><p><ul>'

    for index, group in enumerate(groups_to_print):
        group_name = group.get('name')
        group_url = group.get('url', None)
        html += f'<li><span>{index+1}:</span> <b>'
        if group_url:
            html += f'<a title="{group_name}" href="{group_url}" class="external-link">{group_name}</a>'
        else:
            html += group_name
        html += '</b></li>\n'
    html += '</ul></p>'

    return {
        'pgs_contributors': html
    }


def pgs_ancestry_legend(request) -> str:
    ''' HTML code for the Ancestry legend. '''
    ancestry_labels = constants.ANCESTRY_LABELS
    count = 0
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

    return {
        'ancestry_legend': '''
    <div id="ancestry_legend" class="filter_container">
        <div class="filter_header">Ancestry legend <a class="pgs_no_icon_link info-icon" target="_blank" href="/docs/ancestry/#anc_category" data-toggle="tooltip" data-placement="bottom" title="Click on this icon to see more information about the Ancestry Categories (open in a new tab)"><i class="fas fa-info-circle"></i></a></div>
        <div id="ancestry_legend_content">{}</div>
    </div>'''.format(legend_html)
    }
