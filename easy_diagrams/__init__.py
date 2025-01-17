import os

import sentry_sdk
from pyramid.config import Configurator
from pyramid_auto_env import autoenv_settings
from sentry_sdk.integrations.pyramid import PyramidIntegration

sentry_sdk.init(
    dsn=os.environ.get("SENTRY_DSN"),
    traces_sample_rate=0.1,
    profiles_sample_rate=0.1,
    integrations=[
        PyramidIntegration(
            transaction_style="route_pattern",
        )
    ],
)


# `autoenv_settings`` for overwriting configuration by using environment
# variables for more details see https://pypi.org/project/pyramid-auto-env/
@autoenv_settings(prefix="ED")
def main(global_config, **settings):
    """This function returns a Pyramid WSGI application."""
    if settings["sqlalchemy.url"].startswith("postgres://"):
        # making heroku to work with sqlalchemy, see https://stackoverflow.com/questions/62688256/sqlalchemy-exc-nosuchmoduleerror-cant-load-plugin-sqlalchemy-dialectspostgre
        settings["sqlalchemy.url"] = settings["sqlalchemy.url"].replace(
            "postgres://", "postgresql+psycopg://", 1
        )  # XXX: remove this magic to be replaced with a heroku-run.sh script
    with Configurator(settings=settings) as config:
        config.include("pyramid_chameleon")
        config.include("pyramid_services")
        config.include(".services")
        config.include(".security")
        config.include(".routes")
        config.include(".models")
        config.scan()
    return config.make_wsgi_app()
