from uuid import uuid4

import base36
import pytest

from easy_diagrams import main
from easy_diagrams import models
from easy_diagrams.models.organization import OrganizationTable
from easy_diagrams.models.organization import organization_user_association


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


@pytest.fixture(name="organization_factory")
def organization_factory_fixture(dbsession):
    def create_organization(name=None):
        if name is None:
            name = f"org_{base36.dumps(uuid4().int)}"
        org = OrganizationTable(name=name)
        dbsession.add(org)
        dbsession.flush()
        return org

    yield create_organization


@pytest.fixture(name="organization")
def organization_fixture(organization_factory):
    """Dummy organization for tests."""
    yield organization_factory()


@pytest.fixture(name="user")
def user_fixture(user_factory, organization, dbsession):
    """Dummy user for tests with organization membership."""
    user = user_factory()
    # Add user to organization
    dbsession.execute(
        organization_user_association.insert().values(
            user_id=user.id, organization_id=organization.id, is_owner=True
        )
    )
    dbsession.flush()
    yield user
