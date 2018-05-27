import os
BASE_DIR = os.path.dirname(__file__)

SECRET_KEY = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'tests',
]

MIDDLEWARE = (
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

ROOT_URLCONF = 'tests.urls'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
    }
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'handlers': {
        'airbrake': {
            'level': 'WARNING',
            'class': 'airbrake.handlers.AirbrakeHandler',
            'api_key': 'MY_API_KEY',
            'env_name': 'test',
        }
    },
    'loggers': {
        'test': {
            'handlers': ['airbrake'],
            'level': 'WARNING'
        },
        'django.request': {
            'handlers': ['airbrake'],
            'propagate': True,
            'level': 'WARNING'
        },
    }
}
