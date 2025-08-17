import pytest


@pytest.fixture(scope="function")
def page(browser):
    # Create a new context with a larger viewport
    context = browser.new_context(viewport={"width": 1920, "height": 1480})
    page = context.new_page()
    yield page
    context.close()
