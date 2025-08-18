from uuid import uuid4

import base36
import pytest

from easy_diagrams import main
from easy_diagrams import models
from easy_diagrams.models.organization import OrganizationTable
from easy_diagrams.models.organization import organization_users


@pytest.fixture(scope="session")
def app(app_settings, dbengine):
    """Pyramid WSGI application for the tests with the database engine."""
    return main({}, dbengine=dbengine, **app_settings)


@pytest.fixture(name="user_factory")
def user_factory_fixture(dbsession):
    def create_user(email=None):
        if email is None:
            email = f"user_{base36.dumps(uuid4().int)}@example.com"

        # Create organization first
        org_id = str(uuid4())
        org = OrganizationTable(id=org_id, name=f"{email}'s Organization")
        dbsession.add(org)
        dbsession.flush()

        # Create user
        user = models.User(email=email)
        dbsession.add(user)
        dbsession.flush()

        # Add user to organization as owner
        dbsession.execute(
            organization_users.insert().values(
                organization_id=org_id, user_id=user.id, is_owner=True
            )
        )

        assert user.id is not None
        return user

    yield create_user


@pytest.fixture(name="user")
def user_fixture(user_factory):
    """Dummy user for tests."""
    yield user_factory()
