from django.conf.urls import url
from django.http.response import Http404


class ViewException(Exception):
    pass


def raises_404(request):
    raise Http404


def raises_view_exception(request):
    raise ViewException('Could not find my Django')


def raises_import_error(request):
    import invalid.package.name  # NOQA


urlpatterns = [
    url(r'^raises/404/$', raises_404),
    url(r'^raises/view-exception/$', raises_view_exception),
    url(r'^raises/import-error/$', raises_import_error),
]
