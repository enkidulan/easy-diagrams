import functools

from pyramid.httpexceptions import HTTPFound
from pyramid.request import Request
from pyramid.view import view_config

from easy_diagrams import interfaces
from easy_diagrams.domain.organization import OrganizationEdit
from easy_diagrams.domain.organization import OrganizationID


class OrganizationRepoViewMixin:
    request: Request

    @functools.cached_property
    def organization_repo(self):
        return self.request.find_service(interfaces.IOrganizationRepo)


class OrganizationsView(OrganizationRepoViewMixin):
    def __init__(self, request: Request):
        self.request = request

    @view_config(
        route_name="organizations",
        renderer="../templates/organizations.pt",
        request_method="GET",
    )
    def organizations_list(self):
        """List organizations."""
        organizations = self.organization_repo.list()
        return {"organizations": organizations}

    @view_config(route_name="organizations", request_method="POST")
    def organizations_create(self):
        """Create new organization."""
        name = self.request.POST.get("name", "").strip()
        if not name:
            return HTTPFound(location=self.request.route_url("organizations"))

        self.organization_repo.create(name)
        return HTTPFound(location=self.request.route_url("organizations"))


class OrganizationDetailView(OrganizationRepoViewMixin):
    def __init__(self, request: Request):
        self.request = request

    @view_config(
        route_name="organization_entity",
        renderer="../templates/organization_detail.pt",
        request_method="GET",
    )
    def organization_detail(self):
        """Show organization details."""
        org_id = OrganizationID(self.request.matchdict["organization_id"])

        organization = self.organization_repo.get(org_id)
        users = self.organization_repo.list_users(org_id)

        return {
            "organization": organization,
            "users": users,
        }

    @view_config(route_name="organization_entity", request_method="POST")
    def organization_update(self):
        """Update or delete organization based on method override."""
        org_id = OrganizationID(self.request.matchdict["organization_id"])

        method = self.request.POST.get("_method", "POST")

        if method == "PUT":
            name = self.request.POST.get("name", "").strip()
            if name:
                changes = OrganizationEdit(name=name)
                self.organization_repo.edit(org_id, changes)
            return HTTPFound(
                location=self.request.route_url(
                    "organization_entity", organization_id=org_id.value
                )
            )

        elif method == "DELETE":
            self.organization_repo.delete(org_id)
            return HTTPFound(location=self.request.route_url("organizations"))

        return HTTPFound(
            location=self.request.route_url(
                "organization_entity", organization_id=org_id.value
            )
        )


class OrganizationUsersView(OrganizationRepoViewMixin):
    def __init__(self, request: Request):
        self.request = request

    @view_config(route_name="organization_users", request_method="POST")
    def organization_add_user(self):
        """Add user to organization."""
        org_id = OrganizationID(self.request.matchdict["organization_id"])

        email = self.request.POST.get("email", "").strip()
        is_owner = self.request.POST.get("is_owner") == "on"

        if email:
            try:
                self.organization_repo.add_user(org_id, email, is_owner)
            except ValueError:
                pass  # User already exists, ignore

        return HTTPFound(
            location=self.request.route_url(
                "organization_entity", organization_id=org_id.value
            )
        )


class OrganizationUserView(OrganizationRepoViewMixin):
    def __init__(self, request: Request):
        self.request = request

    @view_config(route_name="organization_user_entity", request_method="POST")
    def organization_user_actions(self):
        """Handle user actions via method override."""
        org_id = OrganizationID(self.request.matchdict["organization_id"])
        user_id = self.request.matchdict["user_id"]

        method = self.request.POST.get("_method", "POST")

        if method == "DELETE":
            self.organization_repo.remove_user(org_id, user_id)
        elif method == "PUT":
            action = self.request.POST.get("action")
            try:
                if action == "make_owner":
                    self.organization_repo.make_owner(org_id, user_id)
                elif action == "remove_owner":
                    self.organization_repo.remove_owner(org_id, user_id)
            except ValueError:
                pass  # Ignore errors (e.g., last owner)

        return HTTPFound(
            location=self.request.route_url(
                "organization_entity", organization_id=org_id.value
            )
        )


def includeme(config):
    config.scan()
