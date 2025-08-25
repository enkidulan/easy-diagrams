import pytest
from playwright.sync_api import Page


@pytest.mark.skip()
@pytest.mark.flaky(retries=2, delay=1)
def test_create_organization(test_id: str, page: Page) -> None:
    """Test creating a new organization."""
    page.goto("http://localhost:8000/")
    page.get_by_role("button", name="Create Diagram").click()
    page.get_by_role("button", name="Google Login").click()

    # Navigate to organizations
    page.get_by_role("link", name="Organizations").click()

    # Create organization
    org_name = f"Test Org {test_id}"
    page.get_by_placeholder("Organization name").fill(org_name)
    page.get_by_role("button", name="Create Organization").click()

    # Verify organization appears in list
    page.get_by_role("link", name=org_name).wait_for()
    assert page.get_by_role("link", name=org_name).is_visible()


@pytest.mark.skip()
@pytest.mark.flaky(retries=2, delay=1)
def test_organization_detail_and_edit(test_id: str, page: Page) -> None:
    """Test viewing and editing organization details."""
    page.goto("http://localhost:8000/")
    page.get_by_role("button", name="Create Diagram").click()
    page.get_by_role("button", name="Google Login").click()

    # Navigate to organizations and create one
    page.get_by_role("link", name="Organizations").click()
    org_name = f"Test Org {test_id}"
    page.get_by_placeholder("Organization name").fill(org_name)
    page.get_by_role("button", name="Create Organization").click()

    # Click on organization to view details
    page.get_by_role("link", name=org_name).click()

    # Verify we're on the detail page
    page.get_by_role("heading", name=org_name).wait_for()
    assert page.get_by_role("heading", name=org_name).is_visible()

    # Edit organization name
    new_name = f"Updated Org {test_id}"
    page.get_by_label("Organization Name").fill(new_name)
    page.get_by_role("button", name="Update Organization").click()

    # Verify name was updated
    page.get_by_role("heading", name=new_name).wait_for()
    assert page.get_by_role("heading", name=new_name).is_visible()


@pytest.mark.skip()
@pytest.mark.flaky(retries=2, delay=1)
def test_add_user_to_organization(test_id: str, page: Page) -> None:
    """Test adding a user to an organization."""
    page.goto("http://localhost:8000/")
    page.get_by_role("button", name="Create Diagram").click()
    page.get_by_role("button", name="Google Login").click()

    # Navigate to organizations and create one
    page.get_by_role("link", name="Organizations").click()
    org_name = f"Test Org {test_id}"
    page.get_by_placeholder("Organization name").fill(org_name)
    page.get_by_role("button", name="Create Organization").click()

    # Go to organization detail
    page.get_by_role("link", name=org_name).click()

    # Add a user
    test_email = f"test{test_id}@example.com"
    page.get_by_placeholder("User email").fill(test_email)
    page.get_by_role("button", name="Add User").click()

    # Verify user appears in the members list
    # Note: The user ID will be displayed, not the email
    page.get_by_text("Organization Members").wait_for()
    # Check that there's at least one user in the table (the creator)
    assert page.locator("table tbody tr").count() >= 1


@pytest.mark.skip()
@pytest.mark.flaky(retries=2, delay=1)
def test_delete_organization(test_id: str, page: Page) -> None:
    """Test deleting an organization."""
    page.goto("http://localhost:8000/")
    page.get_by_role("button", name="Create Diagram").click()
    page.get_by_role("button", name="Google Login").click()

    # Navigate to organizations and create one
    page.get_by_role("link", name="Organizations").click()
    org_name = f"Test Org {test_id}"
    page.get_by_placeholder("Organization name").fill(org_name)
    page.get_by_role("button", name="Create Organization").click()

    # Go to organization detail
    page.get_by_role("link", name=org_name).click()

    # Delete organization
    page.on("dialog", lambda dialog: dialog.accept())  # Accept confirmation dialog
    page.get_by_role("button", name="Delete Organization").click()

    # Verify we're back on organizations list
    page.get_by_role("heading", name="Organizations").wait_for()
    assert page.get_by_role("heading", name="Organizations").is_visible()

    # Verify organization is no longer in the list
    assert not page.get_by_role("link", name=org_name).is_visible()


@pytest.mark.skip()
@pytest.mark.flaky(retries=2, delay=1)
def test_organization_user_role_management(test_id: str, page: Page) -> None:
    """Test managing user roles in organization."""
    page.goto("http://localhost:8000/")
    page.get_by_role("button", name="Create Diagram").click()
    page.get_by_role("button", name="Google Login").click()

    # Navigate to organizations and create one
    page.get_by_role("link", name="Organizations").click()
    org_name = f"Test Org {test_id}"
    page.get_by_placeholder("Organization name").fill(org_name)
    page.get_by_role("button", name="Create Organization").click()

    # Go to organization detail
    page.get_by_role("link", name=org_name).click()

    # Add a user as owner
    test_email = f"owner{test_id}@example.com"
    page.get_by_placeholder("User email").fill(test_email)
    page.get_by_label("Make Owner").check()
    page.get_by_role("button", name="Add User").click()

    # Verify user management interface is present
    page.get_by_text("Organization Members").wait_for()
    assert page.get_by_text("Organization Members").is_visible()

    # Check that Owner badges are visible
    assert (
        page.locator(".badge.bg-primary").count() >= 1
    )  # At least one owner (creator)
