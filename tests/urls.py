from django.conf.urls import patterns, url


class ViewException(Exception):
    pass


def raises(request):
    raise ViewException('Could not find my Django')


urlpatterns = patterns(
    '',
    url(r'^raises/$', raises)
)
