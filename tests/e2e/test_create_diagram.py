import time

import pytest
from playwright.sync_api import Page


@pytest.mark.skip(reason="TODO: fix this")
@pytest.mark.flaky(retries=2, delay=1)
def test_editor_view(test_id: str, page: Page) -> None:
    page.goto("http://localhost:8000/")
    page.get_by_role("button", name="Create Diagram").click()
    page.get_by_role("button", name="Google Login").click()
    page.get_by_role("banner").get_by_role("button", name="Create Diagram").click()

    # TODO: this is dumb, but I need to wait for the page to load and initialize the listeners
    time.sleep(0.5)

    assert not page.locator("#uml").inner_html().strip()

    page.locator("div").filter(has_text="Public view").nth(3).click()
    page.locator("input#title").press_sequentially(f"Diagram {test_id}")

    page.locator(".ace_content").click()
    page.get_by_label("Cursor at row").press_sequentially("bob -> alice: hi")

    page.locator("img#diagram_image").wait_for()
    assert page.locator("img#diagram_image").is_visible()

    page.get_by_role("link", name="My Diagrams").click()

    page.get_by_role("link", name=f"Diagram {test_id}").first.click()
    assert page.locator("#diagram_image").is_visible()


@pytest.mark.skip(reason="TODO: fix this")
@pytest.mark.flaky(retries=2, delay=1)
def test_builtin_view(test_id: str, page: Page) -> None:
    page.goto("http://localhost:8000/")
    page.get_by_role("button", name="Create Diagram").click()
    page.get_by_role("button", name="Google Login").click()
    page.get_by_role("banner").get_by_role("button", name="Create Diagram").click()

    page.goto(page.url.replace("/editor", "/builtin"))

    # TODO: this is dumb, but I need to wait for the page to load and initialize the listeners
    time.sleep(0.5)

    page.locator(".collapsible").click()

    assert not page.locator("#uml").inner_html().strip()

    page.locator("input#title").press_sequentially(f"Diagram {test_id}")

    page.locator(".ace_content").click()
    page.get_by_label("Cursor at row").press_sequentially("bob -> alice: hi")

    page.locator("img#diagram_image").wait_for()
    assert page.locator("img#diagram_image").is_visible()

    page.get_by_role("link", name=f"Diagram {test_id}").click()
    page.goto("http://localhost:8000/diagrams")

    page.get_by_role("link", name=f"Diagram {test_id}").first.click()
    assert page.locator("#diagram_image").is_visible()
