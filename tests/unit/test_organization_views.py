from unittest.mock import Mock
from unittest.mock import PropertyMock
from unittest.mock import patch

from pyramid.httpexceptions import HTTPSeeOther

from easy_diagrams.views.organization import OrganizationEdit


def test_edit_form_get(app_request):
    mock_org_repo = Mock()
    mock_org = Mock()
    mock_users = [Mock()]
    mock_owners = [Mock()]
    mock_org_repo.get_by_user.return_value = mock_org
    mock_org_repo.get_user_organization_id.return_value = "org-123"
    mock_org_repo.get_users.return_value = mock_users
    mock_org_repo.get_owners.return_value = mock_owners

    app_request.find_service = Mock(return_value=mock_org_repo)

    mock_user = Mock()
    mock_user.id = "user-123"
    mock_dbsession = Mock()
    mock_dbsession.query.return_value.get.return_value = mock_user
    app_request.dbsession = mock_dbsession

    with patch.object(
        type(app_request), "authenticated_userid", new_callable=PropertyMock
    ) as mock_auth_id:
        mock_auth_id.return_value = "user-123"

        view = OrganizationEdit(app_request)
        result = view.edit_form()

        expected = {
            "organization": mock_org,
            "users": mock_users,
            "owners": mock_owners,
            "current_user": mock_user,
        }
        assert result == expected
        mock_org_repo.get_by_user.assert_called_once_with("user-123")


def test_update_organization_post(app_request):
    mock_org_repo = Mock()
    mock_org_repo.get_user_organization_id.return_value = "org-123"
    app_request.find_service = Mock(return_value=mock_org_repo)

    mock_user = Mock()
    mock_user.id = "user-123"
    mock_dbsession = Mock()
    mock_dbsession.query.return_value.get.return_value = mock_user
    app_request.dbsession = mock_dbsession

    # Mock the params property
    type(app_request).params = PropertyMock(
        return_value={"action": "update_name", "name": "New Organization Name"}
    )
    app_request.route_url = Mock(return_value="/organization/edit")

    with patch.object(
        type(app_request), "authenticated_userid", new_callable=PropertyMock
    ) as mock_auth_id:
        mock_auth_id.return_value = "user-123"

        view = OrganizationEdit(app_request)
        result = view.update_organization()

        assert isinstance(result, HTTPSeeOther)
        mock_org_repo.update_name.assert_called_once_with(
            "org-123", "New Organization Name"
        )


def test_update_organization_post_no_name(app_request):
    mock_org_repo = Mock()
    mock_org_repo.get_user_organization_id.return_value = "org-123"
    app_request.find_service = Mock(return_value=mock_org_repo)

    mock_user = Mock()
    mock_user.id = "user-123"
    mock_dbsession = Mock()
    mock_dbsession.query.return_value.get.return_value = mock_user
    app_request.dbsession = mock_dbsession

    # Mock the params property with empty dict
    type(app_request).params = PropertyMock(return_value={})
    app_request.route_url = Mock(return_value="/organization/edit")

    with patch.object(
        type(app_request), "authenticated_userid", new_callable=PropertyMock
    ) as mock_auth_id:
        mock_auth_id.return_value = "user-123"

        view = OrganizationEdit(app_request)
        result = view.update_organization()

        assert isinstance(result, HTTPSeeOther)
        mock_org_repo.update_name.assert_not_called()
