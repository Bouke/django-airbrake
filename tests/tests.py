import logging
import xml.etree.ElementTree as etree
from django.http import Http404

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch

from django.conf import settings
from django.contrib.sessions.backends.db import SessionStore
from django.test import TestCase
from django.test.utils import override_settings

import airbrake
from .urls import ViewException
from .utils import xml_compare, xsd_validate


@patch('airbrake.handlers.urlopen', autospec=True)
class XMLDataTest(TestCase):
    def setUp(self):
        self.logger = logging.getLogger('test')

    def test_exception(self, urlopen):
        urlopen.return_value.getcode.return_value = 200

        try:
            raise Exception('Could not find my shoes')
        except Exception as exc:
            self.logger.exception(exc)

        self.assertEqual(urlopen.call_count, 1)
        xml = urlopen.call_args[0][0].data
        xsd_validate(xml)

        self.assertTrue(xml_compare(etree.fromstring("""
        <notice version="2.0">
            <api-key>MY_API_KEY</api-key>
            <notifier>
                <name>django-airbrake</name>
                <version>%(version)s</version>
                <url>http://github.com/Bouke/django-airbrake</url>
            </notifier>
            <server-environment>
                <environment-name>test</environment-name>
            </server-environment>
            <error>
                <class>Exception</class>
                <message>Could not find my shoes: Could not find my shoes</message>
                <backtrace>
                    <line file="*"
                          method="test_exception: raise Exception('Could not find my shoes')"
                          number="*" />
                </backtrace>
            </error>
        </notice>
        """ % {'version': airbrake.__version__}),
            etree.fromstring(xml),
            self.fail))

    def test_django_request(self, urlopen):
        urlopen.return_value.getcode.return_value = 200

        session = SessionStore()
        session['user'] = 'foobunny'
        session.save()
        self.client.cookies[settings.SESSION_COOKIE_NAME] = session.session_key

        try:
            self.client.post('/raises/view-exception/?foo=bar', {'foo2': 'bar2'},
                             HTTP_USER_AGENT='Python/3.3')
        except ViewException:
            pass

        self.assertEqual(urlopen.call_count, 1)
        xml = urlopen.call_args[0][0].data
        xsd_validate(xml)

        # @todo cgi-data has undefined ordering, need to adjust xml validation
        self.assertTrue(xml_compare(etree.fromstring("""
        <notice version="2.0">
            <api-key>MY_API_KEY</api-key>
            <notifier>
                <name>django-airbrake</name>
                <version>%(version)s</version>
                <url>http://github.com/Bouke/django-airbrake</url>
            </notifier>
            <server-environment>
                <environment-name>test</environment-name>
            </server-environment>
            <request>
                <url>http://testserver/raises/view-exception/?foo=bar</url>
                <component>tests.urls.raises_view_exception</component>
                <action>POST</action>
                <params>
                    <var key='foo2'>bar2</var>
                </params>
                <session>
                    <var key='user'>foobunny</var>
                </session>
                <cgi-data>
                    <var key='DJANGO_SETTINGS_MODULE'>tests.settings</var>
                    <var key='HTTP_COOKIE'>sessionid=%(session)s</var>
                    <var key='HTTP_USER_AGENT'>Python/3.3</var>
                    <var key='SERVER_NAME'>testserver</var>
                    <var key='REMOTE_ADDR'>127.0.0.1</var>
                </cgi-data>
            </request>
            <error>
                <class>ViewException</class>
                <message>Internal Server Error: /raises/view-exception/: Could not find my Django</message>
                <backtrace>
                    <line file="*"
                          method="*"
                          number="*" />
                    <line file="*"
                          method="raises_view_exception: raise ViewException('Could not find my Django')"
                          number="*" />
                </backtrace>
            </error>
        </notice>
        """ % {'version': airbrake.__version__, 'session': session.session_key}),
            etree.fromstring(xml),
            self.fail))

    def test_raises_404(self, urlopen):
        urlopen.return_value.getcode.return_value = 200

        try:
            self.client.get('/raises/404/')
        except Http404:
            pass

        self.assertEqual(urlopen.call_count, 0)

    def test_raises_import_error(self, urlopen):
        urlopen.return_value.getcode.return_value = 200

        try:
            self.client.get('/raises/import-error/')
        except ImportError:
            pass

        self.assertEqual(urlopen.call_count, 1)
        xsd_validate(urlopen.call_args[0][0].data)


@patch('airbrake.handlers.urlopen', autospec=True)
@override_settings(INSTALLED_APPS=['tests'], MIDDLEWARE_CLASSES=())
class NoSessionTest(TestCase):
    def test_raises_viewexception(self, urlopen):
        urlopen.return_value.getcode.return_value = 200

        try:
            self.client.get('/raises/view-exception/')
        except ViewException:
            pass

        self.assertEqual(urlopen.call_count, 1)
        xsd_validate(urlopen.call_args[0][0].data)
