import pytest

from easy_diagrams import models
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


def test_get_owners(organization_repo, user):
    """Test getting organization owners."""
    org_id = organization_repo.create("Test Org")

    owners = organization_repo.get_owners(org_id)

    assert len(owners) == 1
    assert str(user.id) in owners


def test_make_owner(organization_repo, other_user):
    """Test making a user an owner."""
    org_id = organization_repo.create("Test Org")
    organization_repo.add_user(org_id, other_user.email, is_owner=False)

    organization_repo.make_owner(org_id, str(other_user.id))

    owners = organization_repo.get_owners(org_id)
    assert str(other_user.id) in owners


def test_remove_owner_with_multiple_owners(organization_repo, user, other_user):
    """Test removing an owner when there are multiple owners."""
    org_id = organization_repo.create("Test Org")
    organization_repo.add_user(org_id, other_user.email, is_owner=True)

    # Should have 2 owners now
    owners = organization_repo.get_owners(org_id)
    assert len(owners) == 2

    # Remove one owner
    organization_repo.remove_owner(org_id, str(other_user.id))

    owners = organization_repo.get_owners(org_id)
    assert len(owners) == 1
    assert str(user.id) in owners
    assert str(other_user.id) not in owners


def test_remove_last_owner_fails(organization_repo, user):
    """Test that removing the last owner fails."""
    org_id = organization_repo.create("Test Org")

    with pytest.raises(ValueError, match="Cannot remove the last owner"):
        organization_repo.remove_owner(org_id, str(user.id))


def test_remove_non_owner_fails(organization_repo, other_user):
    """Test that removing a non-owner fails."""
    org_id = organization_repo.create("Test Org")
    organization_repo.add_user(org_id, other_user.email, is_owner=False)

    with pytest.raises(ValueError, match="is not an owner"):
        organization_repo.remove_owner(org_id, str(other_user.id))


def test_organization_get_no_owners_property(organization_repo, user, other_user):
    """Test that getting an organization does not include owners property."""
    org_id = organization_repo.create("Test Org")
    organization_repo.add_user(org_id, other_user.email, is_owner=True)

    org = organization_repo.get(org_id)

    assert org.id == org_id
    assert org.name == "Test Org"
    assert not hasattr(org, "owners")


def test_delete_removes_all_associations(organization_repo, dbsession, other_user):
    """Test that deleting an organization removes all user associations."""
    org_id = organization_repo.create("Test Org")
    organization_repo.add_user(org_id, other_user.email, is_owner=False)

    # Verify associations exist
    from easy_diagrams.models.organization import organization_user_association

    associations = dbsession.execute(
        organization_user_association.select().where(
            organization_user_association.c.organization_id == org_id.value
        )
    ).fetchall()
    assert len(associations) == 2  # Creator + added user

    # Delete organization
    organization_repo.delete(org_id)

    # Verify all associations are gone
    associations = dbsession.execute(
        organization_user_association.select().where(
            organization_user_association.c.organization_id == org_id.value
        )
    ).fetchall()
    assert len(associations) == 0
