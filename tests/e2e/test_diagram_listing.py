import pytest
from playwright.sync_api import Page
from playwright.sync_api import expect


@pytest.mark.flaky(retries=2, delay=1)
@pytest.mark.xfail(reason="enable later")
def test_diagram_listing_pagination(test_id: str, page: Page) -> None:
    """Tests the diagram listing and pagination."""
    # 1. Login
    page.goto("http://localhost:8000/")
    page.get_by_role("banner").get_by_role("button", name="Create Diagram").click()
    page.get_by_role("button", name="Google Login").click()

    # 2. Create 11 diagrams to trigger pagination
    # The page size is 10, so 11 diagrams will create 2 pages.
    for i in range(11):
        page.get_by_role("banner").get_by_role("button", name="Create Diagram").click()

    page.get_by_role("link", name="My Diagrams").click()

    # 3. We should be on the /diagrams page.
    # Check that the first page shows 10 diagrams.
    diagram_rows = page.locator("#diagrams tbody tr")
    expect(diagram_rows).to_have_count(10)

    # 4. Check pagination controls
    pagination = page.locator(".pagination")
    expect(pagination).to_be_visible()

    # Check page info
    page_info = pagination.get_by_text("Page 1 of 2")
    expect(page_info).to_be_visible()

    # Previous should be disabled, Next should be enabled
    previous_link = pagination.get_by_role("link", name="Previous")
    next_link = pagination.get_by_role("link", name="Next")

    expect(previous_link.locator("..")).to_have_class("page-item disabled")
    expect(next_link).to_be_visible()
    expect(next_link.locator("..")).not_to_have_class("page-item disabled")

    # 5. Click the "Next" button.
    next_link.click()

    # 6. Check that the second page shows 1 diagram.
    expect(diagram_rows).to_have_count(1)

    # Check page info
    page_info = pagination.get_by_text("Page 2 of 2")
    expect(page_info).to_be_visible()

    # 7. Previous should be enabled, Next should not be visible
    expect(previous_link.locator("..")).not_to_have_class("page-item disabled")
    expect(next_link).not_to_be_visible()

    # 8. Click the "Previous" button.
    previous_link.click()

    # 9. Check that we are back on the first page with 10 diagrams.
    expect(diagram_rows).to_have_count(10)
    page_info = pagination.get_by_text("Page 1 of 2")
    expect(page_info).to_be_visible()
