from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.view import view_config


@view_config(
    route_name="home",
    renderer="easy_diagrams:templates/home.pt",
    request_method="GET",
    permission=NO_PERMISSION_REQUIRED,
)
def home_view(request):
    return {"one": "one", "project": "easy_diagrams"}  # TODO: remove this
