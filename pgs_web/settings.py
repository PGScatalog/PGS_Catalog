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
    elif not os.environ['SECRET_KEY']:
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
# Local app installation
if PGS_ON_GAE == 0:
    local_apps = [
        'release.apps.ReleaseConfig',
        'django_extensions'
    ]
    INSTALLED_APPS.extend(local_apps)
# Live app installation
if PGS_ON_LIVE_SITE:
    INSTALLED_APPS.append('corsheaders')


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
    'catalog.context_processors.pgs_info'
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
    # the unix socket at /cloudsql/<your-cloudsql-connection string>
    DATABASES = {
        'default': {
            'ENGINE': DB_ENGINE,
            'NAME': os.environ['DATABASE_NAME'],
            'USER': os.environ['DATABASE_USER'],
            'PASSWORD': os.environ['DATABASE_PASSWORD'],
            'HOST': os.environ['DATABASE_HOST'],
            'PORT': os.environ['DATABASE_PORT']
        }
    }
else:
    # Running locally so connect to either a local PostgreSQL instance or connect
    # to Cloud SQL via the proxy.  To start the proxy via command line:
    # $ cloud_sql_proxy -instances=pgs-catalog:europe-west2:pgs-*******=tcp:5430
    # See https://cloud.google.com/sql/docs/postgres/connect-admin-proxy
    DATABASES = {
        'default': {
            'ENGINE': DB_ENGINE,
            'NAME': os.environ['DATABASE_NAME'],
            'USER': os.environ['DATABASE_USER'],
            'PASSWORD': os.environ['DATABASE_PASSWORD'],
            'HOST': 'localhost',
            'PORT': os.environ['DATABASE_PORT_LOCAL']
        }
    }
# [END db_setup]


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
# CSS, JavaScript, Images
STATIC_URL = '/static/'

STATIC_ROOT = os.path.join(BASE_DIR, "static/")

STATICFILES_FINDERS = [
	'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder'
]


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
#     '127.0.0.1'
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
        'rest_framework.renderers.BrowsableAPIRenderer',
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
    'search.documents.score_ext': 'score_ext',
    'search.documents.efo_trait': 'efo_trait',
    'search.documents.publication': 'publication'
}
