import pytest

from easy_diagrams import models
from easy_diagrams.services.organization_repo import OrganizationRepo


@pytest.fixture
def organization_repo(dbsession, user):
    """Create organization repository for testing."""
    return OrganizationRepo(str(user.id), dbsession)


def test_add_existing_user_by_email(organization_repo, dbsession):
    """Test adding an existing user by email."""
    # Create existing user
    existing_user = models.User(email="existing@example.com")
    dbsession.add(existing_user)
    dbsession.flush()

    org_id = organization_repo.create("Test Org")

    # Add existing user by email
    organization_repo.add_user(org_id, "existing@example.com")

    # Verify user was added
    from easy_diagrams.models.organization import organization_user_association

    association = organization_repo.dbsession.execute(
        organization_user_association.select().where(
            organization_user_association.c.organization_id == org_id.value,
            organization_user_association.c.user_id == existing_user.id,
        )
    ).first()

    assert association is not None
    assert association.is_owner is False


def test_add_new_user_by_email_creates_user(organization_repo, dbsession):
    """Test adding a non-existent user by email creates new user."""
    org_id = organization_repo.create("Test Org")
    new_email = "newuser@example.com"

    # Verify user doesn't exist
    user_before = (
        dbsession.query(models.User).filter(models.User.email == new_email).first()
    )
    assert user_before is None

    # Add user by email
    organization_repo.add_user(org_id, new_email, is_owner=True)

    # Verify user was created
    user_after = (
        dbsession.query(models.User).filter(models.User.email == new_email).first()
    )
    assert user_after is not None
    assert user_after.email == new_email

    # Verify user was added to organization
    from easy_diagrams.models.organization import organization_user_association

    association = organization_repo.dbsession.execute(
        organization_user_association.select().where(
            organization_user_association.c.organization_id == org_id.value,
            organization_user_association.c.user_id == user_after.id,
        )
    ).first()

    assert association is not None
    assert association.is_owner is True


def test_add_same_email_twice_fails(organization_repo):
    """Test adding the same email twice fails."""
    org_id = organization_repo.create("Test Org")
    email = "duplicate@example.com"

    # Add user first time
    organization_repo.add_user(org_id, email)

    # Try to add same email again
    with pytest.raises(ValueError, match="is already in organization"):
        organization_repo.add_user(org_id, email)


def test_add_user_creates_minimal_user_record(organization_repo, dbsession):
    """Test that created users have minimal required fields."""
    org_id = organization_repo.create("Test Org")
    email = "minimal@example.com"

    organization_repo.add_user(org_id, email)

    # Check created user has minimal fields
    user = dbsession.query(models.User).filter(models.User.email == email).first()
    assert user is not None
    assert user.email == email
    assert user.id is not None
    assert user.created_at is not None
    # Other fields should be None/default
    assert user.activated_at is None
    assert user.last_login_at is None
    assert user.enabled is True  # Default value
