import pytest
from sqlalchemy.exc import IntegrityError

from easy_diagrams.models.organization import OrganizationTable
from easy_diagrams.models.organization import organization_users


def test_organization_creation(dbsession):
    org = OrganizationTable(id="test-org", name="Test Organization")
    dbsession.add(org)
    dbsession.flush()

    assert org.id == "test-org"
    assert org.name == "Test Organization"
    assert org.created_at is not None


def test_organization_users_constraint(dbsession, user):
    # Try to add user with non-existent user_id (foreign key constraint)
    from uuid import uuid4

    other_user_id = uuid4()

    # Get user's organization_id from the association table
    result = (
        dbsession.query(organization_users.c.organization_id)
        .filter_by(user_id=user.id)
        .first()
    )
    org_id = result.organization_id

    with pytest.raises(IntegrityError, match="foreign key constraint"):
        dbsession.execute(
            organization_users.insert().values(
                organization_id=org_id, user_id=other_user_id, is_owner=False
            )
        )
        dbsession.flush()


def test_user_organization_relationship(dbsession, user):
    # Test that user has organization relationship
    assert len(user.organizations) > 0
    org = user.organizations[0]
    assert org is not None

    # Test that user is in organization's users
    assert user in org.users
