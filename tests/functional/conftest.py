from uuid import uuid4

import base36
import pytest
import webtest
from pyramid.interfaces import ISecurityPolicy
from pyramid_services import IServiceRegistry
from pyramid_services import ProxyFactory
from webob.cookies import Cookie

from easy_diagrams import interfaces
from easy_diagrams import main
from easy_diagrams import models


@pytest.fixture(scope="session")
def app(app_settings, dbengine):
    """Pyramid WSGI application for the tests with the database engine."""
    return main({}, dbengine=dbengine, **app_settings)


class TestApp(webtest.TestApp):

    def get_cookie(self, name, default=None):
        # webtest currently doesn't expose the unescaped cookie values
        # so we're using webob to parse them for us
        # see https://github.com/Pylons/webtest/issues/171
        cookie = Cookie(
            " ".join(
                "%s=%s" % (c.name, c.value) for c in self.cookiejar if c.name == name
            )
        )

        return next(
            (m.value.decode("latin-1") for m in cookie.values()),
            default,
        )

    def get_csrf_token(self):
        """

        Convenience method to get the current CSRF token.
        This value must be passed to POST/PUT/DELETE requests in either the
        "X-CSRF-Token" header or the "csrf_token" form value.
        testapp.post(..., headers={'X-CSRF-Token': testapp.get_csrf_token()})
        or
        testapp.post(..., {'csrf_token': testapp.get_csrf_token()})
        """

        return self.get_cookie("csrf_token")

    def logout(self, status=303):
        """Convenience method to logout the client."""
        self.post(
            "/logout", headers={"X-CSRF-Token": self.get_csrf_token()}, status=status
        )

    def login(self, user_email="dummy@example.com", status=303):
        """Convenience method to login the client."""
        from easy_diagrams import models
        from easy_diagrams.services.organization_repo import OrganizationRepo

        # Get the app's dbsession from the test environment
        dbsession = self.app.registry.settings.get("app.dbsession")
        if not dbsession:
            # Fallback to getting from extra_environ if not in settings
            dbsession = self.extra_environ.get("app.dbsession")

        # Create or get user
        user = dbsession.query(models.User).filter_by(email=user_email).first()
        if not user:
            user = models.User(email=user_email)
            dbsession.add(user)
            dbsession.flush()

        # Create default organization for user if they don't have one
        org_repo = OrganizationRepo(user.id, dbsession)
        organizations = org_repo.list()
        if not organizations:
            _ = org_repo.create(f"Test Organization for {user_email}")
            dbsession.flush()
            organizations = org_repo.list()

        self.get(
            "/social_login/google",
            status=status,
            headers={"TEST_USER_EMAIL": user_email},
        )
        self.set_cookie(
            "csrf_token", "dummy_csrf_token"
        )  # setting the csrf token again, as it is reset after the redirect


@pytest.fixture(name="user_factory")
def user_factory_fixture(dbsession):
    def create_user(email=None):
        if email is None:
            email = f"user_{base36.dumps(uuid4().int)}@example.com"
        user = models.User(email=email)
        dbsession.add(user)
        dbsession.flush()
        assert user.id is not None
        return user

    yield create_user


@pytest.fixture(name="user")
def user_fixture(user_factory):
    """Dummy user for tests."""
    yield user_factory()


class DummyRenderer:
    def __init__(self, context, request):
        self.context = context
        self.request = request

    def render(self, diagram):
        return b"dummy_image"


@pytest.fixture
def testapp(app, tm, dbsession, request_host) -> TestApp:
    # override request.dbsession and request.tm with our own
    # externally-controlled values that are shared across requests but aborted
    # at the end

    service_registry = app.registry.getUtility(IServiceRegistry)
    # override the diagram renderer with a dummy renderer to avoid calling plantuml
    service_registry.register_factory(
        ProxyFactory(DummyRenderer), interfaces.IDiagramRenderer
    )

    # making sure the csrf token is not secure and has Lax SameSite policy
    # so that test can login and logout
    security_policy = app.registry.getUtility(ISecurityPolicy)
    security_policy.authtkt.secure = False
    security_policy.authtkt.cookie_profile.samesite = "LaX"
    security_policy.authtkt.cookie_profile.secure = False

    testapp = TestApp(
        app,
        extra_environ={
            "HTTP_HOST": request_host,
            "tm.active": True,
            "tm.manager": tm,
            "app.dbsession": dbsession,
        },
    )

    # initialize a csrf token instead of running an initial request to get one
    # from the actual app - this only works using the CookieCSRFStoragePolicy
    testapp.set_cookie("csrf_token", "dummy_csrf_token")

    yield testapp
