from pyramid.authentication import AuthTktCookieHelper
from pyramid.authorization import ACLHelper
from pyramid.authorization import Authenticated
from pyramid.authorization import Everyone
from pyramid.config import Configurator
from pyramid.csrf import CookieCSRFStoragePolicy
from pyramid.csrf import new_csrf_token
from pyramid.httpexceptions import HTTPSeeOther
from pyramid.request import RequestLocalCache
from pyramid.security import forget

from easy_diagrams import models

# 6 months — keep auth and session cookies aligned so org selection survives
# browser restarts while the user remains logged in.
AUTH_COOKIE_MAX_AGE = 15552000

# Routes that authenticated users may access without a selected organization.
ORGANIZATION_EXEMPT_ROUTE_NAMES = frozenset(
    {
        "home",
        "login",
        "logout",
        "social_login",
        "select_organization",
        "static",
        "organizations",
        "organization_entity",
        "organization_users",
        "organization_user_entity",
        "diagram_view_image_png",
        "diagram_view_image_svg",
    }
)


def logout_user(request, location=None):
    request.session.pop("selected_organization_id", None)
    request.session.pop("selected_organization_name", None)
    new_csrf_token(request)
    headers = forget(request)
    if location is None:
        location = request.route_url("login")
    return HTTPSeeOther(location=location, headers=headers)


def require_organization_tween_factory(handler, registry):
    def require_organization_tween(request):
        route = request.matched_route
        if route is None or route.name in ORGANIZATION_EXEMPT_ROUTE_NAMES:
            return handler(request)

        if request.authenticated_userid and not request.session.get(
            "selected_organization_id"
        ):
            return logout_user(request)

        return handler(request)

    return require_organization_tween


class SecurityPolicy:
    def __init__(self, secret):
        self.authtkt = AuthTktCookieHelper(
            secret, samesite="None", secure=True, max_age=AUTH_COOKIE_MAX_AGE
        )
        self.identity_cache = RequestLocalCache(self.load_identity)
        self.acl = ACLHelper()

    def load_identity(self, request):
        identity = self.authtkt.identify(request)
        if identity is None:
            return None

        userid = identity["userid"]
        user = request.dbsession.query(models.User).get(userid)
        return user

    def identity(self, request):
        return self.identity_cache.get_or_create(request)

    def authenticated_userid(self, request):
        user = self.identity(request)
        if user is not None:
            return user.id
        return None

    def remember(self, request, userid, **kw):
        return self.authtkt.remember(request, userid, **kw)

    def forget(self, request, **kw):
        return self.authtkt.forget(request, **kw)

    def permits(self, request, context, permission):
        principals = self.effective_principals(request)
        return self.acl.permits(context, principals, permission)

    def effective_principals(self, request):
        principals = [Everyone]
        user = self.identity(request)
        if user is not None:
            principals.append(Authenticated)
            principals.append("u:" + str(user.id))
        return principals


def includeme(config: Configurator):
    settings = config.get_settings()
    # NOTE: Setting samesite="None" and secure=True to ensure that the app
    #       works in iframe and with HTTPS.
    config.set_csrf_storage_policy(
        CookieCSRFStoragePolicy(samesite="None", secure=True)
    )
    config.set_default_csrf_options(require_csrf=True)
    config.set_security_policy(SecurityPolicy(settings["auth.secret"]))
    config.add_tween("easy_diagrams.security.require_organization_tween_factory")
