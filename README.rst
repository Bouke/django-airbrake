===============
Django Airbrake
===============

.. image:: https://travis-ci.org/Bouke/django-airbrake.png?branch=master
    :alt: Build Status
    :target: https://travis-ci.org/Bouke/django-airbrake

.. image:: https://coveralls.io/repos/Bouke/django-airbrake/badge.png?branch=master
    :alt: Test Coverage
    :target: https://coveralls.io/r/Bouke/django-airbrake?branch=master

.. image:: https://badge.fury.io/py/django-airbrake.png
    :alt: PyPI
    :target: https://pypi.python.org/pypi/django-airbrake

Django Airbrake provides a logging handler to push exceptions and other errors
to airbrakeapp or other airbrake-compatible exception handler services (e.g.
aTech Media's Codebase). Django 1.4, 1.5 and 1.6 are supported on Python 2.6,
2.7, 3.2 and 3.3.

Install version 0.3.0 for Django 1.3 support.

Installation
============

Installation with ``pip``:
::

    $ pip install django-airbrake

Add ``'airbrake.handlers.AirbrakeHandler'`` as a logging handler:
::

    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'filters': {
            'require_debug_false': {
                '()': 'django.utils.log.RequireDebugFalse'
            }
        },
        'handlers': {
            'airbrake': {
                'level': 'WARNING',
                'class': 'airbrake.handlers.AirbrakeHandler',
                'filters': ['require_debug_false'],
                'api_key': '[your-api-key]',
                'env_name': 'develop',
            }
        },
        'loggers': {
            'django.request': {
                'handlers': ['airbrake'],
                'level': 'WARNING',
                'propagate': True,
            },
        }
    }

Settings
========

``level`` (built-in setting)
Change the ``level`` to ``'ERROR'`` to disable logging of 404 error messages.

``api_key`` (required)
    API key provided by the exception handler system.

``env_name`` (required)
    Name of the environment (e.g. production, develop, testing)

``api_url``
    To use aTech Media's Codebase exception system, provide an extra setting
    ``api_url`` with the value
    ``'https://exceptions.codebasehq.com/notifier_api/v2/notices'``.

``env_variables``
    List of environment variables that should be included in the error message,
    defaults to ``['DJANGO_SETTINGS_MODULE']``.

``meta_variables``
    List of ``request.META`` variables that should be included in the error
    message, defaults to ``['HTTP_USER_AGENT', 'HTTP_COOKIE', 'REMOTE_ADDR',
    'SERVER_NAME', 'SERVER_SOFTWARE']``.

``timeout``
    Timeout in seconds to send the error report, defaults to 30 seconds.
