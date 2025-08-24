from unittest.mock import Mock

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


@pytest.fixture
def mock_organization_repo():
    return Mock()


@pytest.fixture
def mock_organization():
    from easy_diagrams.domain.organization import Organization
    from easy_diagrams.domain.organization import OrganizationID

    return Organization(id=OrganizationID("test-id"), name="Test Org")
