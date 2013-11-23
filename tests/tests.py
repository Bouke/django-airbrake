import logging
import xml.etree.ElementTree as etree
try:
    from unittest.mock import patch
except ImportError:
    from mock import patch

from django.conf import settings
from django.contrib.sessions.backends.db import SessionStore
from django.test import TestCase

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

        self.assertTrue(urlopen.call_count, 1)
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
            self.client.post('/raises/?foo=bar', {'foo2': 'bar2'},
                             HTTP_USER_AGENT='Python/3.3')
        except ViewException:
            pass

        self.assertTrue(urlopen.call_count, 1)
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
            <request>
                <url>http://testserver/raises/?foo=bar</url>
                <component>tests.urls.raises</component>
                <action>POST</action>
                <params>
                    <var key='foo'>bar</var>
                    <var key='foo2'>bar2</var>
                </params>
                <session>
                    <var key='user'>foobunny</var>
                </session>
                <cgi-data>
                    <var key='DJANGO_SETTINGS_MODULE'>tests.settings</var>
                    <var key='HTTP_COOKIE'>sessionid=%(session)s</var>
                    <var key='REMOTE_ADDR'>127.0.0.1</var>
                    <var key='HTTP_USER_AGENT'>Python/3.3</var>
                    <var key='SERVER_NAME'>testserver</var>
                </cgi-data>
            </request>
            <error>
                <class>ViewException</class>
                <message>Internal Server Error: /raises/: Could not find my Django</message>
                <backtrace>
                    <line file="*"
                          method="*"
                          number="*" />
                    <line file="*"
                          method="raises: raise ViewException('Could not find my Django')"
                          number="*" />
                </backtrace>
            </error>
        </notice>
        """ % {'version': airbrake.__version__, 'session': session.session_key}),
            etree.fromstring(xml),
            self.fail))
