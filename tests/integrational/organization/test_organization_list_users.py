import pytest

from easy_diagrams import models
from easy_diagrams.services.organization_repo import OrganizationRepo


@pytest.fixture
def organization_repo(dbsession, user):
    """Create organization repository for testing."""
    return OrganizationRepo(str(user.id), dbsession)


@pytest.fixture
def other_users(dbsession):
    """Create multiple users for testing."""
    users = []
    for i in range(5):
        user = models.User(email=f"user{i}@example.com")
        dbsession.add(user)
        dbsession.flush()
        users.append(user)
    return users


def test_list_users_default(organization_repo, user, other_users):
    """Test listing organization users with default pagination."""
    org_id = organization_repo.create("Test Org")

    # Add some users to organization
    for user_obj in other_users[:3]:
        organization_repo.add_user(org_id, user_obj.email)

    users = organization_repo.list_users(org_id)

    assert len(users) == 4  # 3 added + 1 creator


def test_list_users_with_limit(organization_repo, user, other_users):
    """Test listing organization users with custom limit."""
    org_id = organization_repo.create("Test Org")

    # Add users to organization
    for user_obj in other_users:
        organization_repo.add_user(org_id, user_obj.email)

    users = organization_repo.list_users(org_id, limit=3)

    assert len(users) == 3


def test_list_users_with_offset(organization_repo, user, other_users):
    """Test listing organization users with offset."""
    org_id = organization_repo.create("Test Org")

    # Add users to organization
    for user_obj in other_users:
        organization_repo.add_user(org_id, user_obj.email)

    # Get first batch
    first_batch = organization_repo.list_users(org_id, limit=3)
    assert len(first_batch) == 3

    # Get second batch with offset
    second_batch = organization_repo.list_users(org_id, offset=3, limit=3)
    assert len(second_batch) == 3  # 2 remaining + 1 creator


def test_list_users_empty_organization(organization_repo):
    """Test listing users in organization with only creator."""
    org_id = organization_repo.create("Empty Org")

    users = organization_repo.list_users(org_id)

    assert len(users) == 1  # Only creator


def test_list_users_access_denied(dbsession, other_users):
    """Test that users cannot list users of organizations they don't belong to."""
    # Create organization with first user
    repo1 = OrganizationRepo(str(other_users[0].id), dbsession)
    org_id = repo1.create("Private Org")

    # Try to list users with second user
    repo2 = OrganizationRepo(str(other_users[1].id), dbsession)

    with pytest.raises(ValueError, match="not found or access denied"):
        repo2.list_users(org_id)
