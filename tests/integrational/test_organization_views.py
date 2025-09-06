from pyramid.httpexceptions import HTTPFound
from pyramid.testing import DummyRequest

from easy_diagrams.services.organization_repo import OrganizationRepo
from easy_diagrams.views.organizations import OrganizationDetailView
from easy_diagrams.views.organizations import OrganizationsView
from easy_diagrams.views.organizations import OrganizationUsersView
from easy_diagrams.views.organizations import OrganizationUserView


class TestOrganizationsViewIntegration:
    def test_create_and_list_organizations(self, dbsession, user):
        request = DummyRequest()
        request.user = user
        request.dbsession = dbsession
        request.find_service = lambda iface: OrganizationRepo(user.id, dbsession)
        view = OrganizationsView(request)

        # Create organization
        request.POST = {"name": "Test Org"}
        request.route_url = lambda name: f"/{name}"
        result = view.organizations_create()
        assert isinstance(result, HTTPFound)

        # List organizations
        result = view.organizations_list()
        assert len(result["organizations"]) == 2  # 1 created + 1 from fixture
        org_names = {org.name for org in result["organizations"]}
        assert "Test Org" in org_names


class TestOrganizationDetailViewIntegration:
    def test_organization_crud_operations(self, dbsession, user):
        request = DummyRequest()
        request.user = user
        request.dbsession = dbsession
        request.find_service = lambda iface: OrganizationRepo(user.id, dbsession)
        repo = OrganizationRepo(user.id, dbsession)
        org_id = repo.create("Test Org")

        # Get organization detail
        request.matchdict = {"organization_id": str(org_id.value)}
        view = OrganizationDetailView(request)
        result = view.organization_detail()
        assert result["organization"].name == "Test Org"

        # Update organization
        request.POST = {"_method": "PUT", "name": "Updated Org"}
        request.route_url = lambda name, **kwargs: f"/{name}"
        result = view.organization_update()
        assert isinstance(result, HTTPFound)

        # Verify update
        updated_org = repo.get(org_id)
        assert updated_org.name == "Updated Org"


class TestOrganizationUsersViewIntegration:
    def test_add_user_to_organization(self, dbsession, user):
        request = DummyRequest()
        request.user = user
        request.dbsession = dbsession
        request.find_service = lambda iface: OrganizationRepo(user.id, dbsession)
        repo = OrganizationRepo(user.id, dbsession)
        org_id = repo.create("Test Org")

        request.matchdict = {"organization_id": str(org_id.value)}
        request.POST = {"email": "test@example.com", "is_owner": "on"}
        request.route_url = lambda name, **kwargs: f"/{name}"

        view = OrganizationUsersView(request)
        result = view.organization_add_user()
        assert isinstance(result, HTTPFound)

        # Verify user was added
        users = repo.list_users(org_id)
        assert len(users) == 2  # Original user + new user
        assert any(u["email"] == "test@example.com" for u in users)


class TestOrganizationUserViewIntegration:
    def test_user_role_management(self, dbsession, user, user_factory):
        request = DummyRequest()
        request.user = user
        request.dbsession = dbsession
        request.find_service = lambda iface: OrganizationRepo(user.id, dbsession)
        repo = OrganizationRepo(user.id, dbsession)
        org_id = repo.create("Test Org")

        # Add another user
        other_user = user_factory(email="other@example.com")
        repo.add_user(org_id, other_user.email, False)

        request.matchdict = {
            "organization_id": str(org_id.value),
            "user_id": str(other_user.id),
        }
        request.route_url = lambda name, **kwargs: f"/{name}"
        view = OrganizationUserView(request)

        # Make user owner
        request.POST = {"_method": "PUT", "action": "make_owner"}
        result = view.organization_user_actions()
        assert isinstance(result, HTTPFound)

        # Verify user is now owner
        users = repo.list_users(org_id)
        other_user_data = next(u for u in users if u["email"] == other_user.email)
        assert other_user_data["is_owner"] is True

        # Remove user
        request.POST = {"_method": "DELETE"}
        result = view.organization_user_actions()
        assert isinstance(result, HTTPFound)

        # Verify user was removed
        users = repo.list_users(org_id)
        assert len(users) == 1  # Only original user remains
