import pytest

from easy_diagrams import models
from easy_diagrams.services.organization_repo import OrganizationRepo


@pytest.fixture
def organization_repo(dbsession, user):
    """Create organization repository for testing."""
    return OrganizationRepo(str(user.id), dbsession)


def test_list_pagination_default(organization_repo):
    """Test list method with default pagination."""
    # Create multiple organizations
    for i in range(5):
        organization_repo.create(f"Org {i}")

    orgs = organization_repo.list()

    assert (
        len(orgs) == 6
    )  # 5 created + 1 from fixture, all should fit in default limit of 20


def test_list_pagination_with_limit(organization_repo):
    """Test list method with custom limit."""
    # Create multiple organizations
    for i in range(5):
        organization_repo.create(f"Org {i}")

    orgs = organization_repo.list(limit=3)

    assert len(orgs) == 3


def test_list_pagination_with_offset(organization_repo):
    """Test list method with offset."""
    # Create multiple organizations
    org_names = []
    for i in range(5):
        organization_repo.create(f"Org {i}")
        org_names.append(f"Org {i}")

    # Get first 3
    first_batch = organization_repo.list(limit=3)
    assert len(first_batch) == 3

    # Get next 3 with offset (should get remaining 3: 2 created + 1 from fixture)
    second_batch = organization_repo.list(offset=3, limit=3)
    assert len(second_batch) == 3


def test_get_owners_pagination_default(organization_repo, dbsession):
    """Test get_owners with default pagination."""
    org_id = organization_repo.create("Test Org")

    # Add multiple users as owners
    users = []
    for i in range(3):
        user = models.User(email=f"owner{i}@example.com")
        dbsession.add(user)
        dbsession.flush()
        users.append(user)
        organization_repo.add_user(org_id, user.email, is_owner=True)

    owners = organization_repo.get_owners(org_id)

    assert len(owners) == 4  # 3 added + 1 creator


def test_get_owners_pagination_with_limit(organization_repo, dbsession):
    """Test get_owners with custom limit."""
    org_id = organization_repo.create("Test Org")

    # Add multiple users as owners
    for i in range(3):
        user = models.User(email=f"owner{i}@example.com")
        dbsession.add(user)
        dbsession.flush()
        organization_repo.add_user(org_id, user.email, is_owner=True)

    owners = organization_repo.get_owners(org_id, limit=2)

    assert len(owners) == 2


def test_get_owners_pagination_with_offset(organization_repo, dbsession):
    """Test get_owners with offset."""
    org_id = organization_repo.create("Test Org")

    # Add multiple users as owners
    for i in range(3):
        user = models.User(email=f"owner{i}@example.com")
        dbsession.add(user)
        dbsession.flush()
        organization_repo.add_user(org_id, user.email, is_owner=True)

    # Get first 2 owners
    first_batch = organization_repo.get_owners(org_id, limit=2)
    assert len(first_batch) == 2

    # Get remaining owners with offset
    second_batch = organization_repo.get_owners(org_id, offset=2, limit=2)
    assert len(second_batch) == 2  # Should get the remaining 2
