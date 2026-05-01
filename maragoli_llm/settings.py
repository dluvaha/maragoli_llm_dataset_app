"""
Django settings for Maragoli LLM Dataset Collection App
Production-ready configuration
"""

import os
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# Ensure logs directory exists
(BASE_DIR / 'logs').mkdir(parents=True, exist_ok=True)

SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure-maragoli-llm-dataset-collector-change-in-production-x9$k2m!@#'
)

DEBUG = os.environ.get('DJANGO_DEBUG', 'True').lower() == 'true'

ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '*').split(',')

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Local apps
    'datasets.apps.DatasetsConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'maragoli_llm.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'maragoli_llm.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': os.environ.get('DB_ENGINE', 'django.db.backends.sqlite3'),
        'NAME': os.environ.get('DB_NAME', str(BASE_DIR / 'db.sqlite3')),
        'USER': os.environ.get('DB_USER', ''),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', ''),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Nairobi'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ═══════════════════════════════════════════════════════════════════════
# Django Jazzmin — Beautiful Admin Theme                                     │
# ═══════════════════════════════════════════════════════════════════════
JAZZMIN_SETTINGS = {
    # Title bar
    "site_title": "Maragoli LLM Dataset",
    "site_header": "Maragoli LLM Dataset",
    "site_brand": "Maragoli LLM",
    "login_logo": None,
    "login_logo_dark": None,

    # Icons (Font Awesome 5)
    "site_icon": "fas fa-language",

    # UI
    "welcome_sign": True,
    "copyright": "Maragoli LLM Dataset Collection App",

    # Model admin icons
    "model_icon": {
        "datasets.MaragoliDataset": "fas fa-book",
        "datasets.DatasetCategory": "fas fa-tags",
        "datasets.ImportHistory": "fas fa-file-import",
        "auth.User": "fas fa-user",
        "auth.Group": "fas fa-users",
    },

    # Top menu
    "topmenu_links": [
        {"name": "Dashboard", "url": "/", "icon": "fas fa-chart-pie"},
        {"name": "Datasets", "url": "/datasets/", "icon": "fas fa-book"},
        {"name": "Import", "url": "/import/", "icon": "fas fa-file-import"},
        {"name": "Export", "url": "/export/", "icon": "fas fa-download"},
    ],

    # UI tweaks
    "hide_apps": [],
    "hide_models": [],
    "user_avatar": None,
    "show_ui_builder": True,
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": True,
    "footer_text": "Maragoli LLM Dataset Collection App",
    "navbar_fixed": True,
    "sidebar_fixed": True,
    "actions_fixed": True,
    "actions_sticky_top": 0,
}

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

# File upload settings
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{asctime} {levelname} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['file'],
        'level': 'INFO',
    },
}
