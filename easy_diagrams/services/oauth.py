from authomatic import Authomatic
from authomatic.adapters import WebObAdapter
from pyramid.httpexceptions import HTTPNotFound

from easy_diagrams import exceptions
from easy_diagrams import interfaces


class OauthHandler:
    def __init__(self, settings):
        self.config = {
            "google": {
                "class_": "authomatic.providers.oauth2.Google",
                "consumer_key": settings["auth.google.consumer_key"],
                "consumer_secret": settings["auth.google.consumer_secret"],
                "scope": [
                    "https://www.googleapis.com/auth/userinfo.profile",
                    "https://www.googleapis.com/auth/userinfo.email",
                ],
            },
        }
        self.authomatic = Authomatic(self.config, settings["auth.secret"])

    def login(self, provider_name, request, response):
        if provider_name not in self.config:
            raise HTTPNotFound
        adapter = WebObAdapter(request, response)
        result = self.authomatic.login(adapter, provider_name)
        if not result:
            return None
        if result.error:
            raise exceptions.SocialLoginError("Login failed") from result.error
        result.user.update()
        return result.user.email


class DummyOauthHandler:
    def __init__(self, settings):
        self.settings = settings

    def login(self, provider_name, request, response):
        return request.headers.get("TEST_USER_EMAIL") or "dummy@example.com"


def includeme(config):
    settings = config.get_settings()
    handler = (
        DummyOauthHandler
        if settings.get("auth.oauth_handler") == "DummyOauthHandler"
        else OauthHandler
    )
    config.register_service(handler(settings), interfaces.ISocialLoginProvider)
