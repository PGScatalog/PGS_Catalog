"""
Django settings for pgs_web project.
"""

import os

if not os.getenv('GAE_APPLICATION', None):
    app_settings = os.path.join('./', 'app.yaml')
    if os.path.exists(app_settings):
        import yaml
        with open(app_settings) as secrets_file:
            secrets = yaml.load(secrets_file, Loader=yaml.FullLoader)
            for keyword in secrets['env_variables']:
                os.environ[keyword] = secrets['env_variables'][keyword]
    elif 'SECRET_KEY' not in os.environ.keys():
        print("Error: missing secret key")
        exit(1)


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ['SECRET_KEY']

# Define auto field for primary keys (since Django 3.2)
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False
if os.environ['DEBUG'] == 'True':
    DEBUG = True

ALLOWED_HOSTS = os.environ['ALLOWED_HOSTS'].split(',')


#-------#
# Flags #
#-------#
if os.getenv('GAE_APPLICATION', None):
    PGS_ON_GAE = 1
else:
    PGS_ON_GAE = 0

PGS_ON_LIVE_SITE = False
if 'PGS_LIVE_SITE' in os.environ:
    PGS_ON_LIVE_SITE = True if os.environ['PGS_LIVE_SITE'] in ['True', True] else False

PGS_ON_CURATION_SITE = False
if 'PGS_CURATION_SITE' in os.environ:
    PGS_ON_CURATION_SITE = True if os.environ['PGS_CURATION_SITE'] in ['True', True] else False


#------------------------#
# Application definition #
#------------------------#
INSTALLED_APPS = [
	'catalog.apps.CatalogConfig',
    'rest_api.apps.RestApiConfig',
    'search.apps.SearchConfig',
    'benchmark.apps.BenchmarkConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_tables2',
    'compressor',
    'rest_framework',
    'django_elasticsearch_dsl'
]

# Live app installation
if PGS_ON_LIVE_SITE:
    INSTALLED_APPS.append('corsheaders')
# Curation app installation
if PGS_ON_CURATION_SITE:
    INSTALLED_APPS.append('curation_tracker.apps.CurationTrackerConfig')
# Local app installation
if PGS_ON_GAE == 0:
    local_apps = [
        'release.apps.ReleaseConfig',
        'django_extensions'
    ]
    INSTALLED_APPS.extend(local_apps)
# Debug helper
if DEBUG == True:
    INSTALLED_APPS.append('debug_toolbar') # Debug SQL queries


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
# Live middleware
if PGS_ON_LIVE_SITE:
    MIDDLEWARE.insert(2, 'corsheaders.middleware.CorsMiddleware')
# Debug toolbar
if DEBUG == True:
    MIDDLEWARE.insert(5,'debug_toolbar.middleware.DebugToolbarMiddleware') # Debug SQL queries
    # Debug SQL queries
    INTERNAL_IPS = ['127.0.0.1']


ROOT_URLCONF = 'pgs_web.urls'

CONTEXT_PROCESSORS = [
    'django.template.context_processors.debug',
    'django.template.context_processors.request',
    'django.contrib.auth.context_processors.auth',
    'django.contrib.messages.context_processors.messages',
    'catalog.context_processors.pgs_urls',
    'catalog.context_processors.pgs_settings',
    'catalog.context_processors.pgs_search_examples',
    'catalog.context_processors.pgs_browse_examples',
    'catalog.context_processors.pgs_info',
    'catalog.context_processors.pgs_contributors'
]

if PGS_ON_GAE == 1 and DEBUG == False:
    TEMPLATES = [
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [os.path.join(BASE_DIR, 'templates')],
            'OPTIONS': {
                'context_processors': CONTEXT_PROCESSORS,
                'loaders': [
                    ('django.template.loaders.cached.Loader', [
                        'django.template.loaders.filesystem.Loader',
                        'django.template.loaders.app_directories.Loader'
                    ])
                ]
            },
        },
    ]
else:
    TEMPLATES = [
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [],
            'APP_DIRS': True,
            'OPTIONS': {
                'context_processors': CONTEXT_PROCESSORS
            },
        },
    ]


WSGI_APPLICATION = 'pgs_web.wsgi.application'


#----------#
# Database #
#----------#
# [START db_setup]
DB_ENGINE = 'django.db.backends.postgresql'
if PGS_ON_GAE == 1:
    # Running on production App Engine, so connect to Google Cloud SQL using
    # the Cloud SQL proxy via command line, e.g.:
    # $ ./cloud-sql-proxy --address 0.0.0.0 --port 5430 pgs-catalog:europe-west2:pgs-*******
    # See https://cloud.google.com/sql/docs/postgres/connect-auth-proxy
    DATABASES = {
        'default': {
            'ENGINE': DB_ENGINE,
            'NAME': os.environ['DATABASE_NAME'],
            'USER': os.environ['DATABASE_USER'],
            'PASSWORD': os.environ['DATABASE_PASSWORD'],
            'HOST': os.environ['DATABASE_HOST'],
            'PORT': os.environ['DATABASE_PORT']
        },
        'benchmark': {
            'ENGINE': DB_ENGINE,
            'NAME': os.environ['DATABASE_NAME_2'],
            'USER': os.environ['DATABASE_USER_2'],
            'PASSWORD': os.environ['DATABASE_PASSWORD_2'],
            'HOST': os.environ['DATABASE_HOST_2'],
            'PORT': os.environ['DATABASE_PORT_2']
        }
    }
    if PGS_ON_CURATION_SITE:
        DATABASES['curation_tracker'] = {
            'ENGINE': DB_ENGINE,
            'NAME': os.environ['DATABASE_NAME_TRACKER'],
            'USER': os.environ['DATABASE_USER_TRACKER'],
            'PASSWORD': os.environ['DATABASE_PASSWORD_TRACKER'],
            'HOST': os.environ['DATABASE_HOST_TRACKER'],
            'PORT': os.environ['DATABASE_PORT_TRACKER']
        }
else:
    # Running locally so connect to either a local PostgreSQL instance or connect
    # to Cloud SQL via the proxy.
    DATABASES = {
        'default': {
            'ENGINE': DB_ENGINE,
            'NAME': os.environ['DATABASE_NAME'],
            'USER': os.environ['DATABASE_USER'],
            'PASSWORD': os.environ['DATABASE_PASSWORD'],
            'HOST': 'localhost',
            'PORT': os.environ['DATABASE_PORT_LOCAL']
        },
        'benchmark': {
            'ENGINE': DB_ENGINE,
            'NAME': os.environ['DATABASE_NAME_2'],
            'USER': os.environ['DATABASE_USER_2'],
            'PASSWORD': os.environ['DATABASE_PASSWORD_2'],
            'HOST': 'localhost',
            'PORT': os.environ['DATABASE_PORT_LOCAL_2']
        }
    }
    if PGS_ON_CURATION_SITE:
        DATABASES['curation_tracker'] = {
            'ENGINE': DB_ENGINE,
            'NAME': os.environ['DATABASE_NAME_TRACKER'],
            'USER': os.environ['DATABASE_USER_TRACKER'],
            'PASSWORD': os.environ['DATABASE_PASSWORD_TRACKER'],
            'HOST': 'localhost',
            'PORT': os.environ['DATABASE_PORT_LOCAL_TRACKER']
        }
# [END db_setup]


# Router
if PGS_ON_CURATION_SITE:
    DATABASE_ROUTERS = ['routers.db_routers.AuthRouter',]


#---------------------#
# Password validation #
#---------------------#
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


#----------------------#
# Internationalization #
#----------------------#
LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


#--------------#
# Static files #
#--------------#
# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'

STATIC_ROOT = os.path.join(BASE_DIR, "static/")

STATICFILES_FINDERS = [
	'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder'
]
if PGS_ON_GAE == 0:
    STATICFILES_FINDERS.append('compressor.finders.CompressorFinder')


COMPRESS_PRECOMPILERS = ''
COMPRESS_ROOT = os.path.join(BASE_DIR, "static/")

COMPRESS_PRECOMPILERS = (
    ('text/x-scss', 'django_libsass.SassCompiler'),
)


#---------------------#
#  REST API Settings  #
#---------------------#
#REST_SAFELIST_IPS = [
#    '127.0.0.1'
#]
REST_BLACKLIST_IPS = [
    #'127.0.0.1'
]

REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_api.rest_permissions.BlacklistPermission', # see REST_BLACKLIST_IPS
        #'rest_api.rest_permissions.SafelistPermission', # see REST_SAFELIST_IPS
        #'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly'
    ],
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        #'rest_framework.renderers.BrowsableAPIRenderer',
        'rest_api.renderers.NoOptionBrowsableAPIRenderer'
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_api.pagination.CustomPagination',
    'PAGE_SIZE': 50,
    'EXCEPTION_HANDLER': 'rest_api.views.custom_exception_handler',
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES' : {
        'anon': '100/min',
        'user': '100/min'
    }
}


#-----------------#
#  CORS Settings  #
#-----------------#
# CORS_ALLOWED_ORIGIN_REGEXES = [
#     r"^https:\/\/\w+\.ebi\.ac\.uk$"
# ]
CORS_URLS_REGEX = r'^/rest/.*$'
CORS_ALLOW_METHODS = ['GET']
CORS_ALLOW_ALL_ORIGINS = True


#--------------------------#
#  Elasticsearch Settings  #
#--------------------------#
# Elasticsearch configuration
ELASTICSEARCH_DSL = {
    'default': {
        'hosts': os.environ['ELASTICSEARCH_URL_ROOT']
    }
}

# Name of the Elasticsearch index
ELASTICSEARCH_INDEX_NAMES = {
    'search.documents.score': 'score',
    'search.documents.efo_trait': 'efo_trait',
    'search.documents.publication': 'publication'
}


#---------------------------------#
#  Google Cloud Storage Settings  #
#---------------------------------#

if PGS_ON_GAE == 1 and PGS_ON_CURATION_SITE:
    from google.oauth2 import service_account
    GS_CREDENTIALS = service_account.Credentials.from_service_account_file(
        os.path.join(BASE_DIR, os.environ['GS_SERVICE_ACCOUNT_SETTINGS'])
    )
    DEFAULT_FILE_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
    GS_BUCKET_NAME = os.environ['GS_BUCKET_NAME']
    MEDIA_URL = 'https://storage.googleapis.com/'+os.environ['GS_BUCKET_NAME']+'/'
# else:
#     MEDIA_URL = '/media/'
#     MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

MIN_UPLOAD_SIZE=1000
MAX_UPLOAD_SIZE=2000000
MAX_UPLOAD_SIZE_LABEL="2Mb"
DATA_UPLOAD_MAX_NUMBER_FILES=10
