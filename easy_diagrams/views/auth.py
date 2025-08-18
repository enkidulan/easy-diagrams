from datetime import datetime

from pyramid.csrf import new_csrf_token
from pyramid.httpexceptions import HTTPSeeOther
from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.security import forget
from pyramid.security import remember
from pyramid.view import forbidden_view_config
from pyramid.view import view_config

from easy_diagrams import interfaces
from easy_diagrams import models


@view_config(route_name="social_login", permission=NO_PERMISSION_REQUIRED)
def social_login_view(request):
    next_url = request.params.get("next") or request.route_url("home")
    provider_name = request.matchdict.get("provider_name")
    social_oauth = request.find_service(interfaces.ISocialLoginProvider)
    user_email = social_oauth.login(provider_name, request, request.response)
    if not user_email:
        return request.response
    dbsession = request.dbsession
    # TODO: move to service
    user = dbsession.query(models.User).filter_by(email=user_email).first()
    if user is None:
        # Create organization first
        org_repo = request.find_service(interfaces.IOrganizationRepo)

        # Create user
        user = models.User(email=user_email)
        dbsession.add(user)
        dbsession.flush()  # Get user ID

        # Create organization and make user owner
        _ = org_repo.create_for_user(user_email, user.id)
    else:
        user.last_login_at = datetime.now()
    new_csrf_token(request)
    headers = remember(request, user.id)
    return HTTPSeeOther(location=next_url, headers=headers)


@view_config(
    route_name="login",
    request_method="GET",
    renderer="easy_diagrams:templates/login.pt",
    permission=NO_PERMISSION_REQUIRED,
)
def login_view(request):
    next_url = request.params.get("next", request.referrer)
    if not next_url:
        next_url = request.route_url("home")
    return dict(
        url=request.route_url("login"),
        next_url=next_url,
    )


@view_config(
    route_name="logout", request_method="POST", permission=NO_PERMISSION_REQUIRED
)
def logout_view(request):
    next_url = request.route_url("home")
    new_csrf_token(request)
    headers = forget(request)
    return HTTPSeeOther(location=next_url, headers=headers)


@forbidden_view_config(renderer="easy_diagrams:templates/403.pt")
def forbidden_view(exc, request):
    if not request.is_authenticated:
        login_url = request.route_url("login", _query={"next": request.url})
        return HTTPSeeOther(location=login_url)
    request.response.status = 403
    return {}
