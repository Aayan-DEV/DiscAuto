from pathlib import Path
from decouple import config, Csv
from dotenv import load_dotenv
import dj_database_url
import environ
from cryptography.fernet import Fernet
import os

# Load environment variables from .env file if it exists
if not os.getenv('RAILWAY_ENVIRONMENT'):
    load_dotenv()

# Define the base directory
BASE_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = BASE_DIR / 'src'
if str(SRC_DIR) not in os.sys.path:
    os.sys.path.insert(0, str(SRC_DIR))

# Initialise environment variables
env = environ.Env()

# Define the root directory
ROOT_DIR = BASE_DIR.parent

# Read .env file if not in Railway environment
if not os.getenv('RAILWAY_ENVIRONMENT'):
    env.read_env(os.path.join(ROOT_DIR, '.env'))

# Email configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env("EMAIL_HOST", cast=str, default="smtp.gmail.com")
EMAIL_PORT = env("EMAIL_PORT", cast=int, default=587) 
EMAIL_HOST_USER = env("EMAIL_HOST_USER", cast=str, default=None)
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", cast=str, default=None)
EMAIL_USE_TLS = env("EMAIL_USE_TLS", cast=bool, default=True)  
EMAIL_USE_SSL = env("EMAIL_USE_SSL", cast=bool, default=False)  
ADMIN_USER_NAME = config("ADMIN_USER_NAME", default="Admin user")
ADMIN_USER_EMAIL = config("ADMIN_USER_EMAIL", default=None)

MANAGERS = []
ADMINS = []
if all([ADMIN_USER_NAME, ADMIN_USER_EMAIL]):
    ADMINS += [
        (f'{ADMIN_USER_NAME}', f'{ADMIN_USER_EMAIL}')
    ]
    MANAGERS = ADMINS

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config("DJANGO_SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config("DJANGO_DEBUG", cast=bool)
BASE_URL = config("BASE_URL", default=None)
ALLOWED_HOSTS = [
    'localhost', 
    '127.0.0.1', 
    ".railway.app",  # https://discbot.railway.app
    ".ngrok-free.app"
]

if DEBUG:
    ALLOWED_HOSTS += [
        'localhost', '127.0.0.1', ".ngrok-free.app", ".railway.app",
    ]

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'compressor',
    # My-Apps
    "visits",
    'commando',
    "profiles",
    'subscriptions',
    'customers',
    'autoad',
    'autodm',
    'products',
    "ticketbot",
    'colddm',
    'tickets',
    'auths',
    # third-party-apps
    "allauth_ui",
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.discord',
    'allauth.socialaccount.providers.google',
    "widget_tweaks",
    "slippers",
    'django_extensions',
]

SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    "whitenoise.middleware.WhiteNoiseMiddleware",
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    "allauth.account.middleware.AccountMiddleware",
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'discbot.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'discbot.context_processors.subscription_plan',
            ],
        },
    },
]

WSGI_APPLICATION = 'discbot.wsgi.application'

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

CONN_MAX_AGE = config("CONN_MAX_AGE", cast=int, default=300)
DATABASE_URL = config("DATABASE_URL", default=None)

if DATABASE_URL is not None:
    DATABASES = {
        "default": dj_database_url.config(
            default=DATABASE_URL,
            conn_health_checks=True,
            conn_max_age=CONN_MAX_AGE,
        )
    }

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

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

# Django Allauth Config
LOGIN_REDIRECT_URL = "/"
ACCOUNT_AUTHENTICATION_METHOD = "username_email"
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_EMAIL_SUBJECT_PREFIX = "[DiscBot]"
ACCOUNT_EMAIL_REQUIRED = True

AUTHENTICATION_BACKENDS = [
    # Needed to login by username in Django admin, regardless of `allauth`
    'django.contrib.auth.backends.ModelBackend',

    # `allauth` specific authentication methods, such as login by email
    'allauth.account.auth_backends.AuthenticationBackend',
]

SOCIALACCOUNT_PROVIDERS = {
    "discord": {
        "VERIFIED_EMAIL": True
    },
    "google": {
        "VERIFIED_EMAIL": True
    },
}

# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = '/local-cdn/'

# Define the directories that contain static files to be collected
STATICFILES_DIRS = [
    BASE_DIR / "static",  # Custom static files for the app
]

STATICFILES_VENDOR_DIR = BASE_DIR / "static" / "vendors"

# Define where collected static files will be stored
STATIC_ROOT = BASE_DIR / 'local-cdn'

# Storage configuration using WhiteNoise and Compressor
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Compressor settings
COMPRESS_ROOT = STATIC_ROOT
COMPRESS_OUTPUT_DIR = 'CACHE'
COMPRESS_ENABLED = True

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
]

DISCORD_ENCRYPTION_KEY = Fernet.generate_key().decode()

CSRF_TRUSTED_ORIGINS = [
    'https://pet-genuinely-raccoon.ngrok-free.app',
]

# Logging configuration
log_directory = BASE_DIR / 'logs'
if not os.path.exists(log_directory):
    os.makedirs(log_directory)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': log_directory / 'debug.log',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'formatters': {
        'simple': {
            'format': '[%(asctime)s] %(levelname)s %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}


