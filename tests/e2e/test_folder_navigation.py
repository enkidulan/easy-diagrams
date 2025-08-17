import pytest
from playwright.sync_api import Page
from playwright.sync_api import expect


@pytest.mark.flaky(retries=2, delay=1)
def test_folder_creation_and_navigation(test_id: str, page: Page) -> None:
    """Tests folder creation and navigation functionality."""
    # 1. Login
    page.goto("http://localhost:8000/")
    page.get_by_role("banner").get_by_role("button", name="Create Diagram").click()
    page.get_by_role("button", name="Google Login").click()

    # 2. Navigate to diagrams page
    page.get_by_role("link", name="My Diagrams").click()

    # 3. Create a folder
    page.fill("input[name='name']", "Test Folder")
    page.get_by_role("button", name="Create Folder").click()

    # 4. Verify folder appears in listing
    expect(page.locator("text=Test Folder")).to_be_visible()
    expect(page.locator("text=📁")).to_be_visible()

    # 5. Navigate into the folder
    page.get_by_role("link", name="Test Folder").click()

    # 6. Verify we're inside the folder
    expect(page.locator(".breadcrumb")).to_be_visible()
    expect(page.locator("text=Test Folder")).to_be_visible()

    # 7. Create a diagram inside the folder
    page.get_by_role("button", name="Create Diagram").click()

    # 8. Should be redirected to editor
    expect(page).to_have_url(lambda url: "/editor" in url)

    # 9. Go back to folder
    page.get_by_role("link", name="My Diagrams").click()
    page.get_by_role("link", name="Test Folder").click()

    # 10. Verify diagram appears in folder
    diagram_rows = page.locator("#diagrams tbody tr")
    expect(diagram_rows).to_have_count_greater_than(0)


@pytest.mark.flaky(retries=2, delay=1)
def test_nested_folder_creation(test_id: str, page: Page) -> None:
    """Tests creating nested folders."""
    # 1. Login and navigate to diagrams
    page.goto("http://localhost:8000/")
    page.get_by_role("banner").get_by_role("button", name="Create Diagram").click()
    page.get_by_role("button", name="Google Login").click()
    page.get_by_role("link", name="My Diagrams").click()

    # 2. Create parent folder
    page.fill("input[name='name']", "Parent Folder")
    page.get_by_role("button", name="Create Folder").click()

    # 3. Navigate into parent folder
    page.get_by_role("link", name="Parent Folder").click()

    # 4. Create child folder
    page.fill("input[name='name']", "Child Folder")
    page.get_by_role("button", name="Create Folder").click()

    # 5. Verify child folder appears
    expect(page.locator("text=Child Folder")).to_be_visible()

    # 6. Navigate into child folder
    page.get_by_role("link", name="Child Folder").click()

    # 7. Verify breadcrumb shows hierarchy
    expect(page.locator(".breadcrumb")).to_be_visible()


@pytest.mark.flaky(retries=2, delay=1)
def test_folder_diagram_organization(test_id: str, page: Page) -> None:
    """Tests organizing diagrams in folders."""
    # 1. Login and setup
    page.goto("http://localhost:8000/")
    page.get_by_role("banner").get_by_role("button", name="Create Diagram").click()
    page.get_by_role("button", name="Google Login").click()
    page.get_by_role("link", name="My Diagrams").click()

    # 2. Create diagrams in root
    page.get_by_role("button", name="Create Diagram").first.click()
    page.get_by_role("link", name="My Diagrams").click()

    # 3. Create folder
    page.fill("input[name='name']", "Project A")
    page.get_by_role("button", name="Create Folder").click()

    # 4. Create diagram in folder
    page.get_by_role("link", name="Project A").click()
    page.get_by_role("button", name="Create Diagram").click()
    page.get_by_role("link", name="My Diagrams").click()

    # 5. Verify root has both folder and diagram
    expect(page.locator("text=Project A")).to_be_visible()
    expect(page.locator("#diagrams tbody tr")).to_have_count_greater_than(1)

    # 6. Verify folder contains only its diagram
    page.get_by_role("link", name="Project A").click()
    diagram_rows = page.locator("#diagrams tbody tr")
    expect(diagram_rows).to_have_count(1)  # Only the diagram created in folder
