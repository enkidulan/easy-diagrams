from datetime import datetime
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from easy_diagrams import models
from easy_diagrams.models.organization import OrganizationTable


def test_user_email_is_unique(dbsession):
    user1 = models.User(email="unique@example.com")
    dbsession.add(user1)
    dbsession.flush()
    user2 = models.User(email="unique@example.com")
    dbsession.add(user2)
    with pytest.raises(
        IntegrityError, match="duplicate key value violates unique constraint"
    ):
        dbsession.flush()


def test_user_creation(dbsession):
    # Create organization first
    org_id = str(uuid4())
    org = OrganizationTable(id=org_id, name="Test Organization")
    dbsession.add(org)
    dbsession.flush()

    user = models.User(email="newuser@example.com", organization_id=org_id)
    dbsession.add(user)
    dbsession.flush()
    assert user.id is not None
    assert user.email == "newuser@example.com"
    assert user.organization_id == org_id
    assert user.created_at is not None
    assert user.updated_at is None
    assert user.activated_at is None
    assert user.enabled is True
    assert user.last_login_at is None


def test_user_update(dbsession, user):
    user.email = "updated@example.com"
    dbsession.flush()
    assert user.email == "updated@example.com"
    assert user.updated_at is not None


def test_user_enabled_flag(dbsession, user):
    user.enabled = False
    dbsession.flush()
    assert user.enabled is False


def test_user_last_login(dbsession, user):
    now = datetime.now()
    user.last_login_at = now
    dbsession.flush()
    assert user.last_login_at == now
