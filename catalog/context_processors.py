from django.conf import settings
from pgs_web import constants

def pgs_settings(request):
    return {
        'is_pgs_app_on_gae' : settings.PGS_ON_GAE,
        'is_pgs_live_site' : settings.PGS_ON_LIVE_SITE,
        'is_pgs_curation_site': settings.PGS_ON_CURATION_SITE,
        'max_upload_size_label' : settings.MAX_UPLOAD_SIZE_LABEL
    }

def pgs_urls(request):
    return {
        'baker_url'        : constants.USEFUL_URLS['BAKER_URL'],
        'ebi_url'          : constants.USEFUL_URLS['EBI_URL'],
        'hdr_uk_cam_url'   : constants.USEFUL_URLS['HDR_UK_CAM_URL'],
        'pgs_contact'      : constants.USEFUL_URLS['PGS_CONTACT'],
        'pgs_ftp_root'     : constants.USEFUL_URLS['PGS_FTP_ROOT'],
        'pgs_ftp_http_root': constants.USEFUL_URLS['PGS_FTP_HTTP_ROOT'],
        'pgs_ftp_http_meta': constants.USEFUL_URLS['PGS_FTP_HTTP_ROOT']+'/metadata/',
        'pgs_twitter_url'  : constants.USEFUL_URLS['PGS_TWITTER_URL'],
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
        'pgs_citation': constants.PGS_CITATION,
        'pgs_table_helper': constants.TABLE_HELPER
    }
