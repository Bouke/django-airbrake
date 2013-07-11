import logging
import unittest

from lxml import etree
from django import conf
try:
    from django.conf.urls import url, patterns
except ImportError:  # django 1.3
    from django.conf.urls.defaults import url, patterns
from mock import Mock

from airbrake.handlers import AirbrakeHandler
from utils import xml_compare, xsd_validate


class Test(unittest.TestCase):
    def setUp(self):
        self.mock = Mock()

        self.handler = AirbrakeHandler('MY_API_KEY', 'production')
        self.handler._sendMessage = self.mock

        self.logger = logging.getLogger('test')
        self.logger.addHandler(self.handler)

    def test_exception(self):
        try:
            raise Exception('Could not find my shoes')
        except Exception as exc:
            self.logger.exception(exc)
        xml = self.mock.call_args[0][0]

        xsd_validate(etree.fromstring(xml))

        self.assertTrue(xml_compare(etree.fromstring("""
        <notice version="2.0">
            <api-key>MY_API_KEY</api-key>
            <notifier>
                <name>django-airbrake</name>
                <version>1.0.0</version>
                <url>http://github.com/Bouke/django-airbrake</url>
            </notifier>
            <server-environment>
                <environment-name>production</environment-name>
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
        """), etree.fromstring(xml), self.fail))

    def test_django_request(self):
        def myview(request):
            pass
        conf.settings = conf.UserSettingsHolder(Mock(
            ROOT_URLCONF=patterns('', url(r'^test/$', myview)),
        ))

        try:
            raise Exception('Could not find my Django')
        except Exception as exc:
            request = Mock(method='GET', path_info='/test/',
                           build_absolute_uri=lambda: 'http://localhost/test/',
                           REQUEST={'foo': 'bar', 'foo2': 'bar2'},
                           GET={'foo': 'bar'},
                           POST={'foo2': 'bar2'},
                           META={'HTTP_USER_AGENT': 'my test agent'},
                           session={'user': 'foobunny'})
            self.logger.error(str(exc), exc_info=1, extra={'request': request})

        xml = self.mock.call_args[0][0]

        xsd_validate(etree.fromstring(xml))

        self.assertTrue(xml_compare(etree.fromstring("""
        <notice version="2.0">
            <api-key>MY_API_KEY</api-key>
            <notifier>
                <name>django-airbrake</name>
                <version>1.0.0</version>
                <url>http://github.com/Bouke/django-airbrake</url>
            </notifier>
            <server-environment>
                <environment-name>production</environment-name>
            </server-environment>
            <request>
                <url>http://localhost/test/</url>
                <component>%(name)s.myview</component>
                <action>GET</action>
                <params>
                    <var key='foo'>bar</var>
                    <var key='foo2'>bar2</var>
                </params>
                <session>
                    <var key='user'>foobunny</var>
                </session>
                <cgi-data>
                    <var key='HTTP_USER_AGENT'>my test agent</var>
                </cgi-data>
            </request>
            <error>
                <class>Exception</class>
                <message>Could not find my Django: Could not find my Django</message>
                <backtrace>
                    <line file="*"
                          method="test_django_request: raise Exception('Could not find my Django')"
                          number="*" />
                </backtrace>
            </error>
        </notice>
        """ % {'name': __name__}), etree.fromstring(xml), self.fail))

