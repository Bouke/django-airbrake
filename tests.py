import logging
import unittest
from xml.etree.ElementTree import fromstring
from django import conf
try:
    from django.conf.urls import url, patterns
except ImportError:  # django 1.3
    from django.conf.urls.defaults import url, patterns
from mock import Mock
from airbrake.handlers import AirbrakeHandler


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

        self.assertTrue(xml_compare(fromstring("""
        <notice version="2.0">
            <api-key>MY_API_KEY</api-key>
            <notifier>
                <name>django-airbrake</name>
                <version>0.3.0</version>
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
        """), fromstring(xml), self.fail))

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
        self.assertTrue(xml_compare(fromstring("""
        <notice version="2.0">
            <api-key>MY_API_KEY</api-key>
            <notifier>
                <name>django-airbrake</name>
                <version>0.3.0</version>
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
        """ % {'name': __name__}), fromstring(xml), self.fail))


def xml_compare(x1, x2, reporter=None):
    if x1.tag != x2.tag:
        if reporter:
            reporter('Tags do not match: %s and %s' % (x1.tag, x2.tag))
        return False
    for name, value in x1.attrib.items():
        if not text_compare(x2.attrib.get(name), value):
            if reporter:
                reporter('<%s> Attributes do not match: %s=%r, %s=%r'
                         % (x1.tag, name, value, name, x2.attrib.get(name)))
            return False
    for name in x2.attrib.keys():
        if name not in x1.attrib:
            if reporter:
                reporter('<%s> x2 has an attribute x1 is missing: %s'
                         % (x1.tag, name))
            return False
    if not text_compare(x1.text, x2.text):
        if reporter:
            reporter('<%s> text: %r != %r' % (x1.tag, x1.text, x2.text))
        return False
    if not text_compare(x1.tail, x2.tail):
        if reporter:
            reporter('<%s> tail: %r != %r' % (x1.tag, x1.tail, x2.tail))
        return False
    cl1 = x1.getchildren()
    cl2 = x2.getchildren()
    if len(cl1) != len(cl2):
        if reporter:
            reporter('<%s> children length differs, %i != %i'
                     % (x1.tag, len(cl1), len(cl2)))
        return False
    for i, c1 in enumerate(cl1):
        for c2 in cl2:
            if xml_compare(c1, c2):  # no reporter, fail silently
                cl2.remove(c2)
                break
        else:
            if reporter:
                xml_compare(c1, x2.getchildren()[i], reporter=reporter)
                reporter('<%s> children %i do not match: %s'
                         % (x1.tag, i, c1.tag))
            return False
    return True


def text_compare(t1, t2):
    if not t1 and not t2:
        return True
    if t1 == '*' or t2 == '*':
        return True
    return (t1 or '').strip() == (t2 or '').strip()


if __name__ == '__main__':
    unittest.main()
