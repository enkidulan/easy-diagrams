from pyramid.httpexceptions import HTTPSeeOther
from pyramid.request import Request
from pyramid.view import view_config
from pyramid.view import view_defaults

from easy_diagrams import interfaces


@view_defaults(route_name="organization_edit")
class OrganizationEdit:
    def __init__(self, request: Request):
        self.request = request
        self.organization_repo = request.find_service(interfaces.IOrganizationRepo)

    @view_config(
        request_method="GET",
        renderer="easy_diagrams:templates/organization_edit.pt",
    )
    def edit_form(self):
        from easy_diagrams.models.user import User

        user = self.request.dbsession.query(User).get(self.request.authenticated_userid)
        organization = self.organization_repo.get_by_user(user.id)
        org_id = self.organization_repo.get_user_organization_id(user.id)
        users = self.organization_repo.get_users(org_id)
        owners = self.organization_repo.get_owners(org_id)
        return {
            "organization": organization,
            "users": users,
            "owners": owners,
            "current_user": user,
        }

    @view_config(request_method="POST")
    def update_organization(self):
        from easy_diagrams.models.user import User

        user = self.request.dbsession.query(User).get(self.request.authenticated_userid)
        org_id = self.organization_repo.get_user_organization_id(user.id)

        action = self.request.params.get("action")

        if action == "update_name":
            name = self.request.params.get("name")
            if name:
                self.organization_repo.update_name(org_id, name)

        elif action == "add_owner":
            email = self.request.params.get("email")
            if email:
                self.organization_repo.add_owner(org_id, email)

        elif action == "remove_owner":
            owner_id = self.request.params.get("owner_id")
            if owner_id:
                self.organization_repo.remove_owner(org_id, owner_id)

        elif action == "add_user":
            email = self.request.params.get("email")
            if email:
                self.organization_repo.add_user(org_id, email)

        return HTTPSeeOther(location=self.request.route_url("organization_edit"))
