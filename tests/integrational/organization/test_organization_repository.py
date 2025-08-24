from uuid import uuid4

import pytest

from easy_diagrams import models
from easy_diagrams.domain.organization import OrganizationEdit
from easy_diagrams.domain.organization import OrganizationID
from easy_diagrams.services.organization_repo import OrganizationRepo


@pytest.fixture
def organization_repo(dbsession, user):
    """Create organization repository for testing."""
    return OrganizationRepo(str(user.id), dbsession)


@pytest.fixture
def other_user(dbsession):
    """Create another user for testing."""
    user = models.User(email="other@example.com")
    dbsession.add(user)
    dbsession.flush()
    return user


def test_create_organization(organization_repo, dbsession):
    """Test creating an organization."""
    org_id = organization_repo.create("Test Organization")

    assert org_id is not None
    assert isinstance(org_id, OrganizationID)

    # Verify organization exists in database
    org = (
        dbsession.query(models.OrganizationTable)
        .filter(models.OrganizationTable.id == org_id.value)
        .first()
    )
    assert org is not None
    assert org.name == "Test Organization"


def test_get_organization(organization_repo):
    """Test getting an organization."""
    org_id = organization_repo.create("Get Test Org")
    org = organization_repo.get(org_id)

    assert org.id == org_id
    assert org.name == "Get Test Org"


def test_get_nonexistent_organization(organization_repo):
    """Test getting a non-existent organization."""
    fake_id = OrganizationID(uuid4())

    with pytest.raises(ValueError, match="not found or access denied"):
        organization_repo.get(fake_id)


def test_list_organizations(organization_repo):
    """Test listing organizations."""
    # Create multiple organizations
    organization_repo.create("Org 1")
    organization_repo.create("Org 2")

    orgs = organization_repo.list()

    assert len(orgs) == 2
    org_names = {org.name for org in orgs}
    assert "Org 1" in org_names
    assert "Org 2" in org_names


def test_edit_organization(organization_repo):
    """Test editing an organization."""
    org_id = organization_repo.create("Original Name")

    changes = OrganizationEdit(name="Updated Name")
    updated_org = organization_repo.edit(org_id, changes)

    assert updated_org.name == "Updated Name"

    # Verify in database
    retrieved_org = organization_repo.get(org_id)
    assert retrieved_org.name == "Updated Name"


def test_delete_organization(organization_repo, dbsession):
    """Test deleting an organization."""
    org_id = organization_repo.create("To Delete")

    organization_repo.delete(org_id)

    # Verify organization is deleted
    org = (
        dbsession.query(models.OrganizationTable)
        .filter(models.OrganizationTable.id == org_id.value)
        .first()
    )
    assert org is None


def test_add_user_to_organization(organization_repo, other_user):
    """Test adding a user to organization."""
    org_id = organization_repo.create("Multi User Org")

    organization_repo.add_user(org_id, other_user.email, is_owner=False)

    # Verify user was added
    from easy_diagrams.models.organization import organization_user_association

    association = organization_repo.dbsession.execute(
        organization_user_association.select().where(
            organization_user_association.c.organization_id == org_id.value,
            organization_user_association.c.user_id == other_user.id,
        )
    ).first()

    assert association is not None
    assert association.is_owner is False


def test_add_nonexistent_user(organization_repo):
    """Test adding a non-existent user creates new user."""
    org_id = organization_repo.create("Test Org")
    new_email = "newuser@example.com"

    # Should not raise error, should create new user
    organization_repo.add_user(org_id, new_email)

    # Verify user was created and added
    from easy_diagrams.models.organization import organization_user_association

    association = organization_repo.dbsession.execute(
        organization_user_association.select().where(
            organization_user_association.c.organization_id == org_id.value
        )
    ).fetchall()

    assert len(association) == 2  # Creator + new user


def test_add_user_twice(organization_repo, other_user):
    """Test adding the same user twice to organization."""
    org_id = organization_repo.create("Test Org")

    organization_repo.add_user(org_id, other_user.email)

    with pytest.raises(ValueError, match="User .* is already in organization"):
        organization_repo.add_user(org_id, other_user.email)


def test_remove_user_from_organization(organization_repo, other_user):
    """Test removing a user from organization."""
    org_id = organization_repo.create("Test Org")
    organization_repo.add_user(org_id, other_user.email)

    organization_repo.remove_user(org_id, str(other_user.id))

    # Verify user was removed
    from easy_diagrams.models.organization import organization_user_association

    association = organization_repo.dbsession.execute(
        organization_user_association.select().where(
            organization_user_association.c.organization_id == org_id.value,
            organization_user_association.c.user_id == other_user.id,
        )
    ).first()

    assert association is None


def test_make_owner_existing_user(organization_repo, other_user):
    """Test making an existing user an owner."""
    org_id = organization_repo.create("Test Org")
    organization_repo.add_user(org_id, other_user.email, is_owner=False)

    # Make user an owner
    organization_repo.make_owner(org_id, str(other_user.id))

    # Verify owner status
    from easy_diagrams.models.organization import organization_user_association

    association = organization_repo.dbsession.execute(
        organization_user_association.select().where(
            organization_user_association.c.organization_id == org_id.value,
            organization_user_association.c.user_id == other_user.id,
        )
    ).first()

    assert association.is_owner is True


def test_user_isolation(dbsession, user, other_user):
    """Test that users can only access their own organizations."""
    # Create organization with first user
    repo1 = OrganizationRepo(str(user.id), dbsession)
    org_id = repo1.create("User 1 Org")

    # Try to access with second user
    repo2 = OrganizationRepo(str(other_user.id), dbsession)

    with pytest.raises(ValueError, match="not found or access denied"):
        repo2.get(org_id)

    # Second user should see empty list
    orgs = repo2.list()
    assert len(orgs) == 0
