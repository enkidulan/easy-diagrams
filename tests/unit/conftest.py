import pytest
from pyramid.scripting import prepare


@pytest.fixture
def app_request(app, request_host):
    """
    A real request.

    This request is almost identical to a real request but it has some
    drawbacks in tests as it's harder to mock data and is heavier.

    """
    with prepare(registry=app.registry) as env:
        request = env["request"]
        request.host = request_host
        yield request
