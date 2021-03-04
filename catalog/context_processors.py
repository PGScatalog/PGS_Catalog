from django.conf import settings

def pgs_settings(request):
    return {
        'is_pgs_app_on_gae' : settings.PGS_ON_GAE,
        'is_pgs_live_site' : settings.PGS_ON_LIVE_SITE,
        'is_pgs_curation_site' : settings.PGS_ON_CURATION_SITE
    }

def pgs_urls(request):
    return {
        'baker_url'        : settings.USEFUL_URLS['BAKER_URL'],
        'ebi_url'          : settings.USEFUL_URLS['EBI_URL'],
        'hdr_uk_cam_url'   : settings.USEFUL_URLS['HDR_UK_CAM_URL'],
        'pgs_contact'      : settings.USEFUL_URLS['PGS_CONTACT'],
        'pgs_ftp_root'     : settings.USEFUL_URLS['PGS_FTP_ROOT'],
        'pgs_ftp_http_root': settings.USEFUL_URLS['PGS_FTP_HTTP_ROOT'],
        'pgs_twitter_url'  : settings.USEFUL_URLS['PGS_TWITTER_URL'],
        'uoc_url'          : settings.USEFUL_URLS['UOC_URL'],
        'terms_of_use'     : settings.USEFUL_URLS['TERMS_OF_USE'],
        'catalog_publication_url': settings.USEFUL_URLS['CATALOG_PUBLICATION_URL'],
    }

def pgs_search_examples(request):
    eg_count = 0
    html = ''
    # Build the list of search examples
    for example in settings.SEARCH_EXAMPLES:
        link = f'<a href="/search?q={example}">{example}</a>'
        eg_count += 1
        if eg_count > 1:
            if eg_count == 3:
                html += '<span class="extra_example">'
            html += ', '
        html += link
    if eg_count > 2:
        html += '</span>'
    return {
        'pgs_search_examples': html
    }

def pgs_info(request):
    return {
        'pgs_citation': settings.PGS_CITATION
    }
