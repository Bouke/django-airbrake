import logging
import traceback
try:
    from urllib.request import Request, urlopen
    from urllib.error import HTTPError
except ImportError:
    from urllib2 import Request, urlopen, HTTPError
import os
from xml.etree.ElementTree import Element, tostring, SubElement
try:
    from django.core.urlresolvers import resolve
except ImportError:  # Must be Django Version >=2.0
    from django.urls import resolve
from django.http import Http404

from airbrake import __version__, __app_name__, __app_url__

# Adapted from Pulse Energy's AirbrakePy
# https://github.com/pulseenergy/airbrakepy
# Changes for django compatibility by Bouke Haarsma

_DEFAULT_API_URL = 'https://airbrakeapp.com/notifier_api/v2/notices'
_DEFAULT_ENV_VARIABLES = ['DJANGO_SETTINGS_MODULE', ]
_DEFAULT_META_VARIABLES = ['HTTP_USER_AGENT', 'HTTP_COOKIE', 'REMOTE_ADDR',
                           'SERVER_NAME', 'SERVER_SOFTWARE', ]


class AirbrakeHandler(logging.Handler):
    def __init__(self, api_key, env_name, api_url=_DEFAULT_API_URL,
                 timeout=30, env_variables=_DEFAULT_ENV_VARIABLES,
                 meta_variables=_DEFAULT_META_VARIABLES):
        logging.Handler.__init__(self)
        self.api_key = api_key
        self.api_url = api_url
        self.env_name = env_name
        self.env_variables = env_variables
        self.meta_variables = meta_variables
        self.timeout = timeout

    def emit(self, record):
        self._sendMessage(self._generate_xml(record))

    def _generate_xml(self, record):
        exn = None
        trace = None
        if record.exc_info:
            _, exn, trace = record.exc_info

        message = record.getMessage()
        if exn:
            message = "{0}: {1}".format(message, str(exn))

        xml = Element('notice', dict(version='2.0'))
        SubElement(xml, 'api-key').text = self.api_key

        notifier = SubElement(xml, 'notifier')
        SubElement(notifier, 'name').text = __app_name__
        SubElement(notifier, 'version').text = __version__
        SubElement(notifier, 'url').text = __app_url__

        server_env = SubElement(xml, 'server-environment')
        SubElement(server_env, 'environment-name').text = self.env_name

        if hasattr(record, 'request'):
            request = record.request
            try:
                match = resolve(request.path_info)
            except Http404:
                match = None

            request_xml = SubElement(xml, 'request')
            SubElement(request_xml, 'url').text = request.build_absolute_uri()

            if match:
                SubElement(request_xml, 'component').text = "%s.%s" % \
                    (match.func.__module__, match.func.__name__)
                SubElement(request_xml, 'action').text = request.method

            params = SubElement(request_xml, 'params')
            for key, value in request.POST.items():
                SubElement(params, 'var', dict(key=key)).text = str(value)

            session = SubElement(request_xml, 'session')
            for key, value in getattr(request, 'session', {}).items():
                SubElement(session, 'var', dict(key=key)).text = str(value)

            cgi_data = SubElement(request_xml, 'cgi-data')
            for key, value in os.environ.items():
                if key in self.env_variables:
                    SubElement(cgi_data, 'var', dict(key=key)).text = str(value)
            for key, value in request.META.items():
                if key in self.meta_variables:
                    SubElement(cgi_data, 'var', dict(key=key)).text = str(value)

        error = SubElement(xml, 'error')
        SubElement(error, 'class').text = exn.__class__.__name__ if exn else ''
        SubElement(error, 'message').text = message

        backtrace = SubElement(error, 'backtrace')
        if trace is None:
            SubElement(backtrace, 'line', dict(file=record.pathname,
                                               number=str(record.lineno),
                                               method=record.funcName))
        else:
            for pathname, lineno, funcName, text in traceback.extract_tb(trace):
                SubElement(backtrace, 'line', dict(file=pathname,
                                                   number=str(lineno),
                                                   method='%s: %s' % (funcName,
                                                                      text)))

        return tostring(xml)

    def _sendHttpRequest(self, headers, message):
        request = Request(self.api_url, message, headers)
        try:
            response = urlopen(request, timeout=self.timeout)
            status = response.getcode()
        except HTTPError as e:
            status = e.code
        return status

    def _sendMessage(self, message):
        headers = {"Content-Type": "text/xml"}
        status = self._sendHttpRequest(headers, message)
        if status == 200:
            return

        if status == 403:
            exceptionMessage = "Unable to send using SSL"
        elif status == 422:
            exceptionMessage = "Invalid XML sent: {0}".format(message)
        elif status == 500:
            exceptionMessage = "Destination server is unavailable. " \
                               "Please check the remote server status."
        elif status == 503:
            exceptionMessage = "Service unavailable. You may be over your " \
                               "quota."
        else:
            exceptionMessage = "Unexpected status code {0}".format(str(status))

        # @todo log this message, but prevent circular logging
        raise Exception('[django-airbrake] %s' % exceptionMessage)
