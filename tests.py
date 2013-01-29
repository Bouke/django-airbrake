import logging
import unittest
from django import conf
from django.conf.urls import url, patterns
from mock import Mock
from airbrake.handlers import AirbrakeHandler
import airbrake


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

        self.assertIn('<api-key>%s</api-key>' % 'MY_API_KEY', xml)
        self.assertIn('<name>%s</name>' % airbrake.__app_name__, xml)
        self.assertIn('<version>%s</version>' % airbrake.__version__, xml)
        self.assertIn('<url>%s</url>' % airbrake.__app_url__, xml)

        self.assertIn('<environment-name>%s</environment-name>' % 'production',
                      xml)
        self.assertIn('<class>Exception</class>', xml)
        self.assertIn('<message>Could not find my shoes: Could not find my sho'
                      'es</message>', xml)
        self.assertIn('<backtrace><line file="%s" method="test_exception: raise'
                      ' Exception(\'Could not find my shoes\')" number="25" />'
                      % __file__, xml)

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
                           REQUEST={}, GET={}, POST={}, META={}, session={})
            self.logger.error(str(exc), exc_info=1, extra={'request': request})

        xml = self.mock.call_args[0][0]
        self.assertIn('<url>http://localhost/test/</url>', xml)
        self.assertIn('<component>tests.myview</component>', xml)
        self.assertIn('<action>GET</action>', xml)

if __name__ == '__main__':
    unittest.main()
