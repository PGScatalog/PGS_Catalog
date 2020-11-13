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
        'catalog_publication_url': settings.USEFUL_URLS['CATALOG_PUBLICATION_URL'],
    }

def pgs_search_examples(request):
    return {
        'pgs_search_examples': '<a href="/search?q=breast cancer">breast cancer</a>, <a href="/search?q=glaucoma">glaucoma</a><span class="extra_example">, <a href="/search?q=EFO_0001645">EFO_0001645</a></span>'
    }
