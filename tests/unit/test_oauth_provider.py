import pytest
from authomatic.core import LoginResult
from authomatic.exceptions import FailureError
from pyramid.httpexceptions import HTTPNotFound

from easy_diagrams import exceptions
from easy_diagrams.services.oauth import OauthHandler


@pytest.fixture
def settings():
    return {
        "auth.google.consumer_key": "test_key",
        "auth.google.consumer_secret": "test_secret",
        "auth.secret": "test_secret",
    }


@pytest.fixture
def oauth_handler(settings):
    return OauthHandler(settings)


@pytest.fixture
def mock_request():
    class MockRequest:
        def __init__(self):
            self.params = {}
            self.cookies = {}
            self.headers = {}

    return MockRequest()


@pytest.fixture
def mock_response():
    class MockResponse:
        def __init__(self):
            self.headers = {}

    return MockResponse()


def test_login_with_invalid_provider(oauth_handler, mock_request, mock_response):
    with pytest.raises(HTTPNotFound):
        oauth_handler.login("invalid_provider", mock_request, mock_response)


def test_login_with_valid_provider_success(
    mocker, oauth_handler, mock_request, mock_response
):
    mock_user = mocker.Mock()
    mock_user.email = "test@example.com"
    mock_result = mocker.Mock(spec=LoginResult)
    mock_result.user = mock_user
    mock_result.error = None
    mocker.patch.object(oauth_handler.authomatic, "login", return_value=mock_result)
    mocker.patch.object(mock_user, "update")

    email = oauth_handler.login("google", mock_request, mock_response)
    assert email == "test@example.com"
    mock_user.update.assert_called_once()


def test_login_with_valid_provider_failure(
    mocker, oauth_handler, mock_request, mock_response
):
    mock_result = mocker.Mock(spec=LoginResult)
    mock_result.error = FailureError("Login failed")
    mocker.patch.object(oauth_handler.authomatic, "login", return_value=mock_result)

    with pytest.raises(exceptions.SocialLoginError, match="Login failed"):
        oauth_handler.login("google", mock_request, mock_response)


def test_login_with_valid_provider_no_result(
    mocker, oauth_handler, mock_request, mock_response
):
    mocker.patch.object(oauth_handler.authomatic, "login", return_value=None)

    result = oauth_handler.login("google", mock_request, mock_response)
    assert result is None
