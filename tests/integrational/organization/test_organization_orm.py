import pytest
from sqlalchemy.exc import IntegrityError

from easy_diagrams import models


def test_organization_creation(dbsession):
    """Test organization creation."""
    org = models.OrganizationTable(name="Test Organization")
    dbsession.add(org)
    dbsession.flush()

    assert org.id is not None
    assert org.name == "Test Organization"
    assert org.created_at is not None
    assert org.updated_at is None


def test_organization_update(dbsession):
    """Test organization update."""
    org = models.OrganizationTable(name="Original Name")
    dbsession.add(org)
    dbsession.flush()

    org.name = "Updated Name"
    dbsession.flush()

    assert org.name == "Updated Name"
    assert org.updated_at is not None


def test_organization_user_association(dbsession):
    """Test organization-user association."""
    # Create user and organization
    user = models.User(email="test@example.com")
    org = models.OrganizationTable(name="Test Org")
    dbsession.add_all([user, org])
    dbsession.flush()

    # Add user to organization
    from easy_diagrams.models.organization import organization_user_association

    dbsession.execute(
        organization_user_association.insert().values(
            organization_id=org.id, user_id=user.id, is_owner=True
        )
    )
    dbsession.flush()

    # Verify association
    association = dbsession.execute(
        organization_user_association.select().where(
            organization_user_association.c.organization_id == org.id
        )
    ).first()

    assert association is not None
    assert association.user_id == user.id
    assert association.is_owner is True


def test_organization_user_association_cascade_delete(dbsession):
    """Test that deleting organization removes associations."""
    # Create user and organization
    user = models.User(email="test@example.com")
    org = models.OrganizationTable(name="Test Org")
    dbsession.add_all([user, org])
    dbsession.flush()

    # Add user to organization
    from easy_diagrams.models.organization import organization_user_association

    dbsession.execute(
        organization_user_association.insert().values(
            organization_id=org.id, user_id=user.id, is_owner=False
        )
    )
    dbsession.flush()

    # Delete organization
    dbsession.delete(org)
    dbsession.flush()

    # Verify association is gone
    association = dbsession.execute(
        organization_user_association.select().where(
            organization_user_association.c.organization_id == org.id
        )
    ).first()

    assert association is None


def test_organization_name_required(dbsession):
    """Test that organization name is required."""
    org = models.OrganizationTable()
    dbsession.add(org)

    with pytest.raises(IntegrityError, match="null value in column"):
        dbsession.flush()


def test_multiple_users_in_organization(dbsession):
    """Test multiple users can belong to same organization."""
    # Create users and organization
    user1 = models.User(email="user1@example.com")
    user2 = models.User(email="user2@example.com")
    org = models.OrganizationTable(name="Multi User Org")
    dbsession.add_all([user1, user2, org])
    dbsession.flush()

    # Add both users to organization
    from easy_diagrams.models.organization import organization_user_association

    dbsession.execute(
        organization_user_association.insert().values(
            [
                {"organization_id": org.id, "user_id": user1.id, "is_owner": True},
                {"organization_id": org.id, "user_id": user2.id, "is_owner": False},
            ]
        )
    )
    dbsession.flush()

    # Verify both associations exist
    associations = dbsession.execute(
        organization_user_association.select().where(
            organization_user_association.c.organization_id == org.id
        )
    ).fetchall()

    assert len(associations) == 2
    user_ids = {assoc.user_id for assoc in associations}
    assert user1.id in user_ids
    assert user2.id in user_ids
