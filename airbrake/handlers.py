import logging
import traceback
import urllib2
import os
import xmlbuilder

from django.core.urlresolvers import resolve
from django.http import Http404

from airbrake import __version__, __name__, __url__

# Adapted from Pulse Energy's AirbrakePy
# https://github.com/pulseenergy/airbrakepy
# Changes for django compatibility by Bouke Haarsma

_DEFAULT_API_URL = "https://airbrakeapp.com/notifier_api/v2/notices"
_DEFAULT_ENV_VARIABLES = ["DJANGO_SETTINGS_MODULE",]

class AirbrakeHandler(logging.Handler):
    def __init__(self, api_key, env_name, api_url=_DEFAULT_API_URL,
                 timeout=30, env_variables=_DEFAULT_ENV_VARIABLES):
        logging.Handler.__init__(self)
        self.api_key = api_key
        self.api_url = api_url
        self.env_name = env_name
        self.env_variables = env_variables
        self.logger = logging.getLogger(__name__)
        self.timeout = timeout

    def emit(self, record):
        self._sendMessage(self._generate_xml(record))

    def _generate_xml(self, record):
        exn = None
        trace = None
        if record.exc_info:
            _, exn, trace = record.exc_info

        request = None
        if record.request:
            request = record.request

        match = None
        if request:
            try:
                match = resolve(request.path_info)
            except Http404:
                pass

        message = record.getMessage()
        if exn:
            message = "{0}: {1}".format(message, str(exn))

        xml = xmlbuilder.XMLBuilder()
        with xml.notice(version=2.0):
            xml << ('api-key', self.api_key)
            with xml.notifier:
                xml << ('name', __name__)
                xml << ('version', __version__)
                xml << ('url', __url__)
            with xml('server-environment'):
                xml << ('environment-name', self.env_name)
                # (project-root | app-version)
            if request:
                with xml.request:
                    xml << ("url", request.build_absolute_uri())
                    if match:
                        xml << ("component", match.url_name)
                        xml << ("action", request.method)
                    with xml.params:
                        [xml << ('var', value, {'key': key})
                            for key, value in request.REQUEST.items()]
                    with xml.session:
                        [xml << ('var', str(value), {'key': key})
                            for key, value in request.session.items()]
                    with xml('cgi-data'):
                        [xml << ('var', value, {'key': key})
                            for key, value in os.environ.items()
                            if key in self.env_variables]

            with xml.error:
                xml << ('class', exn.__class__.__name__ if exn else '')
                xml << ('message', message)
                with xml.backtrace:
                    if trace is None:
                        [xml << ('line', {'file': record.pathname,
                                          'number': record.lineno,
                                          'method': record.funcName})]
                    else:
                        [xml << ('line', {'file': filename,
                                          'number': line_number,
                                          'method': "{0}: {1}".format(function_name, text)})
                         for filename, line_number, function_name, text in traceback.extract_tb(trace)]
        return str(xml)

    def _sendHttpRequest(self, headers, message):
        request = urllib2.Request(self.api_url, message, headers)
        try:
            response = urllib2.urlopen(request, timeout=self.timeout)
            status = response.getcode()
        except urllib2.HTTPError as e:
            status = e.code
        return status

    def _sendMessage(self, message):
        headers = {"Content-Type": "text/xml"}
        status = self._sendHttpRequest(headers, message)
        if status == 200 or status == 201:
            return

        exceptionMessage = "Unexpected status code {0}".format(str(status))

        if status == 403:
            exceptionMessage = "Unable to send using SSL"
        elif status == 422:
            exceptionMessage = "Invalid XML sent: {0}".format(message)
        elif status == 500:
            exceptionMessage = "Destination server is unavailable. Please check the remote server status."
        elif status == 503:
            exceptionMessage = "Service unavailable. You may be over your quota."

        raise StandardError(exceptionMessage)
