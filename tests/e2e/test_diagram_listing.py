import pytest
from playwright.sync_api import Page
from playwright.sync_api import expect


@pytest.mark.skip()
@pytest.mark.flaky(retries=2, delay=1)
def test_diagram_listing_pagination(test_id: str, page: Page) -> None:
    """Tests the diagram listing and pagination."""
    # 1. Login
    page.goto("http://localhost:8000/")
    page.get_by_role("button", name="Create Diagram").first.click()
    page.get_by_role("button", name="Google Login").click()

    # 2. Create 11 diagrams to trigger pagination
    for i in range(11):
        page.get_by_role("button", name="Create Diagram").first.click()

    page.get_by_role("link", name="My Diagrams").click()

    # 3. Check that the first page shows 10 diagrams
    diagram_rows = page.locator("#diagrams tbody tr").filter(has_text="📄")
    expect(diagram_rows).to_have_count(10)

    # 4. Check pagination controls
    pagination = page.locator(".pagination")
    expect(pagination).to_be_visible()

    page_info = pagination.get_by_text("Page 1 of 2")
    page_info.scroll_into_view_if_needed()
    expect(page_info).to_be_visible()

    previous_link = pagination.get_by_role("link", name="Previous")
    previous_link.scroll_into_view_if_needed()
    expect(previous_link.locator("..")).to_have_class("page-item disabled")

    next_link = pagination.get_by_role("link", name="Next")
    next_link.scroll_into_view_if_needed()
    expect(next_link).to_be_visible()

    # 5. Click Next
    next_link.click()

    # 6. Check second page shows 1 diagram
    diagram_rows = page.locator("#diagrams tbody tr").filter(has_text="📄")
    expect(diagram_rows).to_have_count(1)

    page_info = pagination.get_by_text("Page 2 of 2")
    page_info.scroll_into_view_if_needed()
    expect(page_info).to_be_visible()

    # 7. Previous should be enabled, Next should not be visible
    expect(previous_link.locator("..")).not_to_have_class("page-item disabled")
    expect(next_link).to_have_count(0)

    # 8. Click Previous
    previous_link.click()

    # 9. Check back on first page with 10 diagrams
    diagram_rows = page.locator("#diagrams tbody tr").filter(has_text="📄")
    expect(diagram_rows).to_have_count(10)
    page_info = pagination.get_by_text("Page 1 of 2")
    page_info.scroll_into_view_if_needed()
    expect(page_info).to_be_visible()


@pytest.mark.skip()
@pytest.mark.flaky(retries=2, delay=1)
def test_folder_pagination(test_id: str, page: Page) -> None:
    """Tests pagination within folders."""
    # 1. Login
    page.goto("http://localhost:8000/")
    page.get_by_role("button", name="Create Diagram").first.click()
    page.get_by_role("button", name="Google Login").click()
    page.get_by_role("link", name="My Diagrams").click()

    # 2. Create a folder
    page.fill("input[name='name']", "Test Folder")
    page.get_by_role("button", name="Create Folder").click()

    # 3. Navigate into folder
    page.get_by_role("link", name="Test Folder").click()

    # 4. Create 11 diagrams in folder
    for i in range(11):
        page.get_by_role("button", name="Create Diagram").click()
        page.get_by_role("link", name="My Diagrams").click()
        page.get_by_role("link", name="Test Folder").click()

    # 5. Check pagination in folder
    diagram_rows = page.locator("#diagrams tbody tr").filter(has_text="📄")
    expect(diagram_rows).to_have_count(10)

    pagination = page.locator(".pagination")
    expect(pagination).to_be_visible()

    next_link = pagination.get_by_role("link", name="Next")
    next_link.click()

    # 6. Check second page in folder
    diagram_rows = page.locator("#diagrams tbody tr").filter(has_text="📄")
    expect(diagram_rows).to_have_count(1)

    # 7. Verify we're still in the folder (breadcrumb should be visible)
    expect(page.locator(".breadcrumb")).to_be_visible()
    expect(page.get_by_text("Test Folder")).to_be_visible()
