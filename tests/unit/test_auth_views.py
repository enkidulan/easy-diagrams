from unittest.mock import Mock
from unittest.mock import PropertyMock
from unittest.mock import patch

from pyramid.httpexceptions import HTTPSeeOther

from easy_diagrams.views.auth import social_login_view


def test_social_login_new_user_creates_organization(app_request):
    # Mock services
    mock_social_oauth = Mock()
    mock_social_oauth.login.return_value = "newuser@example.com"

    mock_org_repo = Mock()
    mock_org_repo.create_for_user.return_value = "org-123"

    mock_dbsession = Mock()
    mock_dbsession.query.return_value.filter_by.return_value.first.return_value = None

    app_request.find_service = Mock(
        side_effect=lambda interface: {
            "ISocialLoginProvider": mock_social_oauth,
            "IOrganizationRepo": mock_org_repo,
        }.get(interface.__name__)
    )

    app_request.dbsession = mock_dbsession
    app_request.matchdict = {"provider_name": "google"}
    type(app_request).params = PropertyMock(return_value={})
    app_request.route_url = Mock(return_value="/")

    with patch("easy_diagrams.views.auth.models") as mock_models, patch(
        "easy_diagrams.views.auth.new_csrf_token"
    ), patch("easy_diagrams.views.auth.remember", return_value={}):

        mock_user = Mock()
        mock_user.id = "user-123"
        mock_models.User.return_value = mock_user

        result = social_login_view(app_request)

        # Verify organization was created for user
        mock_org_repo.create_for_user.assert_called_once_with(
            "newuser@example.com", "user-123"
        )

        assert isinstance(result, HTTPSeeOther)
