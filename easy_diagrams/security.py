from pyramid.authentication import AuthTktCookieHelper
from pyramid.authorization import ACLHelper
from pyramid.authorization import Authenticated
from pyramid.authorization import Everyone
from pyramid.config import Configurator
from pyramid.csrf import CookieCSRFStoragePolicy
from pyramid.request import RequestLocalCache

from easy_diagrams import models


class SecurityPolicy:
    def __init__(self, secret):
        self.authtkt = AuthTktCookieHelper(
            secret, samesite="None", secure=True, max_age=15552000
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
    # TODO: samesite="None" is set here for the sake of the builtin view that
    #       has to work in iframe, but samesite="None" defeats the purpose
    #       of the csrf token... it should be set to "Lax" for the rest, so
    #       see if csrf can be configured per view, as only a single view that
    #       handles put-request has to work within the iframe.
    config.set_csrf_storage_policy(
        CookieCSRFStoragePolicy(samesite="None", secure=True)
    )
    config.set_default_csrf_options(require_csrf=True)
    config.set_security_policy(SecurityPolicy(settings["auth.secret"]))
