from django.conf import settings

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
    }
