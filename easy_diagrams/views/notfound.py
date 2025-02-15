from pyramid.view import notfound_view_config
from pyramid.view import view_config

from easy_diagrams.exceptions import DiagramNotFoundError


@notfound_view_config(renderer="easy_diagrams:templates/404.pt")
def notfound_view(request):
    request.response.status = 404
    return {}


@view_config(context=DiagramNotFoundError, renderer="easy_diagrams:templates/404.pt")
def diagram_notfound_view(request):
    request.response.status = 404
    return {}
