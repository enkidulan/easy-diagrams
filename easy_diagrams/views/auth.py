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
from easy_diagrams.services.organization_repo import OrganizationRepo


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
        user = models.User(email=user_email)
        dbsession.add(user)
        dbsession.flush()
    else:
        user.last_login_at = datetime.now()

    # Check user's organizations
    org_repo = OrganizationRepo(user.id, dbsession)
    organizations = org_repo.list()

    new_csrf_token(request)
    headers = remember(request, user.id)

    # If user has multiple organizations, redirect to selection page
    if len(organizations) > 1:
        return HTTPSeeOther(
            location=request.route_url(
                "select_organization", _query={"next": next_url}
            ),
            headers=headers,
        )
    # If user has exactly one organization, set it in session
    elif len(organizations) == 1:
        request.session["selected_organization_id"] = str(organizations[0].id.value)
        request.session["selected_organization_name"] = organizations[0].name

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
    # Clear organization session data
    request.session.pop("selected_organization_id", None)
    request.session.pop("selected_organization_name", None)
    new_csrf_token(request)
    headers = forget(request)
    return HTTPSeeOther(location=next_url, headers=headers)


@view_config(
    route_name="select_organization",
    request_method="GET",
    renderer="easy_diagrams:templates/select_organization.pt",
)
def select_organization_view(request):
    next_url = request.params.get("next", request.route_url("home"))
    org_repo = OrganizationRepo(request.authenticated_userid, request.dbsession)
    organizations = org_repo.list()
    return {
        "organizations": organizations,
        "next_url": next_url,
    }


@view_config(
    route_name="select_organization",
    request_method="POST",
)
def select_organization_post(request):
    next_url = request.params.get("next", request.route_url("home"))
    organization_id = request.POST.get("organization_id")

    if organization_id:
        org_repo = OrganizationRepo(request.authenticated_userid, request.dbsession)
        try:
            from easy_diagrams.domain.organization import OrganizationID

            org = org_repo.get(OrganizationID(organization_id))
            request.session["selected_organization_id"] = organization_id
            request.session["selected_organization_name"] = org.name
        except ValueError:
            # Invalid organization ID, redirect back to selection
            return HTTPSeeOther(
                location=request.route_url(
                    "select_organization", _query={"next": next_url}
                )
            )

    return HTTPSeeOther(location=next_url)


@forbidden_view_config(renderer="easy_diagrams:templates/403.pt")
def forbidden_view(exc, request):
    if not request.is_authenticated:
        login_url = request.route_url("login", _query={"next": request.url})
        return HTTPSeeOther(location=login_url)
    request.response.status = 403
    return {}
