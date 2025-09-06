from pyramid.httpexceptions import HTTPFound
from pyramid.testing import DummyRequest

from easy_diagrams.domain.organization import OrganizationID
from easy_diagrams.views.organizations import OrganizationDetailView
from easy_diagrams.views.organizations import OrganizationsView
from easy_diagrams.views.organizations import OrganizationUsersView
from easy_diagrams.views.organizations import OrganizationUserView


class TestOrganizationsView:
    def test_organizations_list(self, mock_organization_repo):
        request = DummyRequest()
        view = OrganizationsView(request)
        view.organization_repo = mock_organization_repo

        result = view.organizations_list()

        mock_organization_repo.list.assert_called_once()
        assert "organizations" in result

    def test_organizations_create_success(self, mock_organization_repo):
        request = DummyRequest(POST={"name": "Test Org"})
        request.route_url = lambda name: f"/{name}"
        view = OrganizationsView(request)
        view.organization_repo = mock_organization_repo

        result = view.organizations_create()

        mock_organization_repo.create.assert_called_once_with("Test Org")
        assert isinstance(result, HTTPFound)

    def test_organizations_create_empty_name(self, mock_organization_repo):
        request = DummyRequest(POST={"name": ""})
        request.route_url = lambda name: f"/{name}"
        view = OrganizationsView(request)
        view.organization_repo = mock_organization_repo

        result = view.organizations_create()

        mock_organization_repo.create.assert_not_called()
        assert isinstance(result, HTTPFound)


class TestOrganizationDetailView:
    def test_organization_detail(self, mock_organization_repo, mock_organization):
        request = DummyRequest(matchdict={"organization_id": "test-id"})
        view = OrganizationDetailView(request)
        view.organization_repo = mock_organization_repo
        mock_organization_repo.get.return_value = mock_organization
        mock_organization_repo.list_users.return_value = []

        result = view.organization_detail()

        mock_organization_repo.get.assert_called_once()
        mock_organization_repo.list_users.assert_called_once()
        assert result["organization"] == mock_organization

    def test_organization_update_put(self, mock_organization_repo):
        request = DummyRequest(
            matchdict={"organization_id": "test-id"},
            POST={"_method": "PUT", "name": "Updated Name"},
        )
        request.route_url = lambda name, **kwargs: f"/{name}"
        view = OrganizationDetailView(request)
        view.organization_repo = mock_organization_repo

        result = view.organization_update()

        mock_organization_repo.edit.assert_called_once()
        assert isinstance(result, HTTPFound)

    def test_organization_update_delete(self, mock_organization_repo):
        request = DummyRequest(
            matchdict={"organization_id": "test-id"}, POST={"_method": "DELETE"}
        )
        request.route_url = lambda name: f"/{name}"
        view = OrganizationDetailView(request)
        view.organization_repo = mock_organization_repo

        result = view.organization_update()

        mock_organization_repo.delete.assert_called_once()
        assert isinstance(result, HTTPFound)


class TestOrganizationUsersView:
    def test_organization_add_user(self, mock_organization_repo):
        request = DummyRequest(
            matchdict={"organization_id": "test-id"},
            POST={"email": "test@example.com", "is_owner": "on"},
        )
        request.route_url = lambda name, **kwargs: f"/{name}"
        view = OrganizationUsersView(request)
        view.organization_repo = mock_organization_repo

        result = view.organization_add_user()

        mock_organization_repo.add_user.assert_called_once_with(
            OrganizationID("test-id"), "test@example.com", True
        )
        assert isinstance(result, HTTPFound)

    def test_organization_add_user_empty_email(self, mock_organization_repo):
        request = DummyRequest(
            matchdict={"organization_id": "test-id"}, POST={"email": ""}
        )
        request.route_url = lambda name, **kwargs: f"/{name}"
        view = OrganizationUsersView(request)
        view.organization_repo = mock_organization_repo

        result = view.organization_add_user()

        mock_organization_repo.add_user.assert_not_called()
        assert isinstance(result, HTTPFound)


class TestOrganizationUserView:
    def test_organization_user_actions_delete(self, mock_organization_repo):
        request = DummyRequest(
            matchdict={"organization_id": "test-id", "user_id": "user-id"},
            POST={"_method": "DELETE"},
        )
        request.route_url = lambda name, **kwargs: f"/{name}"
        view = OrganizationUserView(request)
        view.organization_repo = mock_organization_repo

        result = view.organization_user_actions()

        mock_organization_repo.remove_user.assert_called_once_with(
            OrganizationID("test-id"), "user-id"
        )
        assert isinstance(result, HTTPFound)

    def test_organization_user_actions_make_owner(self, mock_organization_repo):
        request = DummyRequest(
            matchdict={"organization_id": "test-id", "user_id": "user-id"},
            POST={"_method": "PUT", "action": "make_owner"},
        )
        request.route_url = lambda name, **kwargs: f"/{name}"
        view = OrganizationUserView(request)
        view.organization_repo = mock_organization_repo

        result = view.organization_user_actions()

        mock_organization_repo.make_owner.assert_called_once_with(
            OrganizationID("test-id"), "user-id"
        )
        assert isinstance(result, HTTPFound)

    def test_organization_user_actions_remove_owner(self, mock_organization_repo):
        request = DummyRequest(
            matchdict={"organization_id": "test-id", "user_id": "user-id"},
            POST={"_method": "PUT", "action": "remove_owner"},
        )
        request.route_url = lambda name, **kwargs: f"/{name}"
        view = OrganizationUserView(request)
        view.organization_repo = mock_organization_repo

        result = view.organization_user_actions()

        mock_organization_repo.remove_owner.assert_called_once_with(
            OrganizationID("test-id"), "user-id"
        )
        assert isinstance(result, HTTPFound)
