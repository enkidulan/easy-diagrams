from uuid import uuid4

import base36
import pytest

from easy_diagrams import main
from easy_diagrams import models


@pytest.fixture(scope="session")
def app(app_settings, dbengine):
    """Pyramid WSGI application for the tests with the database engine."""
    return main({}, dbengine=dbengine, **app_settings)


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
