from unittest.mock import Mock
from unittest.mock import PropertyMock

from pyramid.httpexceptions import HTTPSeeOther

from easy_diagrams.views.organization import OrganizationEdit


def test_edit_form_get(app_request):
    mock_org_repo = Mock()
    mock_org = Mock()
    mock_org_repo.get_by_user.return_value = mock_org
    app_request.find_service = Mock(return_value=mock_org_repo)
    app_request.user = Mock()
    app_request.user.id = "user-123"

    view = OrganizationEdit(app_request)
    result = view.edit_form()

    assert result == {"organization": mock_org}
    mock_org_repo.get_by_user.assert_called_once_with("user-123")


def test_update_organization_post(app_request):
    mock_org_repo = Mock()
    app_request.find_service = Mock(return_value=mock_org_repo)
    app_request.user = Mock()
    app_request.user.organization_id = "org-123"

    # Mock the params property
    type(app_request).params = PropertyMock(
        return_value={"name": "New Organization Name"}
    )
    app_request.route_url = Mock(return_value="/diagrams")

    view = OrganizationEdit(app_request)
    result = view.update_organization()

    assert isinstance(result, HTTPSeeOther)
    mock_org_repo.update_name.assert_called_once_with(
        "org-123", "New Organization Name"
    )


def test_update_organization_post_no_name(app_request):
    mock_org_repo = Mock()
    app_request.find_service = Mock(return_value=mock_org_repo)
    app_request.user = Mock()

    # Mock the params property with empty dict
    type(app_request).params = PropertyMock(return_value={})
    app_request.route_url = Mock(return_value="/diagrams")

    view = OrganizationEdit(app_request)
    result = view.update_organization()

    assert isinstance(result, HTTPSeeOther)
    mock_org_repo.update_name.assert_not_called()
