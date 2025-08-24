from dataclasses import dataclass

from pyramid.config import Configurator
from pyramid.request import Request
from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.security import Allow
from pyramid.security import Authenticated


@dataclass
class RootFactory:
    """Basic root factory for ensuring that only authenticated users can access the application."""

    __acl__ = [(Allow, Authenticated, "view")]
    request: Request = None


def includeme(config: Configurator):
    # security
    config.set_root_factory(RootFactory)
    config.set_default_permission(
        "view"
    )  # ensure only users with `view` permission can access endpoints
    # static
    config.add_static_view(
        "static", "static", cache_max_age=3600, permission=NO_PERMISSION_REQUIRED
    )
    # landing page
    config.add_route("home", "/")
    # authentication
    config.add_route("login", "/login")
    config.add_route("logout", "/logout")
    config.add_route("social_login", "/social_login/{provider_name}")
    # diagrams
    config.add_route("diagrams", "/diagrams")
    config.add_route("diagram_entity", "/diagrams/{diagram_id}")
    config.add_route("diagram_view_editor", "/diagrams/{diagram_id}/editor")
    config.add_route("diagram_view_builtin", "/diagrams/{diagram_id}/builtin")
    config.add_route("diagram_view_json", "/diagrams/{diagram_id}/json")
    config.add_route("diagram_view_image_png", "/diagrams/{diagram_id}/image.png")
    # SVG is old deprecated format, now using PNG, but keeping it for compatibility
    config.add_route("diagram_view_image_svg", "/diagrams/{diagram_id}/image.svg")
    # organizations
    config.add_route("organizations", "/organizations")
    config.add_route("organization_entity", "/organizations/{organization_id}")
    config.add_route("organization_users", "/organizations/{organization_id}/users")
    config.add_route(
        "organization_user_entity", "/organizations/{organization_id}/users/{user_id}"
    )
