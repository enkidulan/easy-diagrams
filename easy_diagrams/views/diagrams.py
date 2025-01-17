import functools
from dataclasses import dataclass

from pydantic import ValidationError
from pyramid.httpexceptions import HTTPBadRequest
from pyramid.httpexceptions import HTTPNotFound
from pyramid.httpexceptions import HTTPSeeOther
from pyramid.request import Request
from pyramid.response import Response
from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.view import view_config
from pyramid.view import view_defaults

from easy_diagrams import exceptions
from easy_diagrams import interfaces
from easy_diagrams.domain.diagram import Diagram
from easy_diagrams.domain.diagram import DiagramEdit


@dataclass
class DiagramsRepoViewMixin:

    request: Request

    @functools.cached_property
    def diagram_repo(self):
        return self.request.find_service(interfaces.IDiagramRepo)


@view_defaults(route_name="diagrams")
class Diagrams(DiagramsRepoViewMixin):

    @view_config(
        request_method="POST",
    )
    def create_diagram(self):
        diagram_id = self.diagram_repo.create()
        return HTTPSeeOther(
            location=self.request.route_url(
                "diagram_view_editor", diagram_id=diagram_id, _query={"new": "true"}
            )
        )

    @view_config(
        request_method="GET",
        renderer="easy_diagrams:templates/diagrams.pt",
    )
    def list_diagrams(self):
        return {"diagrams_listing": self.diagram_repo.list()}


class DiagramResourceMixin(DiagramsRepoViewMixin):

    @property
    def requested_diagram_id(self):
        return self.request.matchdict.get("diagram_id")

    @property
    def diagram(self):
        try:
            return self.diagram_repo.get(self.requested_diagram_id)
        except exceptions.DiagramNotFoundError:
            raise HTTPNotFound()


@view_defaults(request_method="GET")
class DiagramViews(DiagramResourceMixin):

    @view_config(
        route_name="diagram_view_editor",
        renderer="easy_diagrams:templates/diagram.pt",
    )
    def editor_page(self):
        return {"diagram": self.diagram}

    @view_config(
        route_name="diagram_view_builtin",
        renderer="easy_diagrams:templates/diagram_builtin.pt",
    )
    def builtin_editor(self):
        return {"diagram": self.diagram}

    @view_config(
        route_name="diagram_view_json",
        renderer="json",
    )
    def json_view(self):
        return {
            "id": self.diagram.id,
            "title": self.diagram.title,
            "is_public": self.diagram.is_public,
            "code": self.diagram.code,
        }

    @view_config(
        route_name="diagram_view_image",
        permission=NO_PERMISSION_REQUIRED,
    )
    def rendered_image(self):
        try:
            image = self.diagram_repo.get_image_render(self.requested_diagram_id)
        except exceptions.DiagramNotFoundError:
            raise HTTPNotFound()
        response = Response(body=image)
        response.content_type = "image/svg+xml"
        response.headers["Content-Disposition"] = (
            f"filename={self.requested_diagram_id}.svg"
        )
        return response


@view_defaults(route_name="diagram_entity")
class DiagramEntity(DiagramResourceMixin):

    @view_config(
        request_method="PUT",
        renderer="easy_diagrams:templates/image.pt",
    )
    def diagram_update(self):
        try:
            changes = DiagramEdit(**self.request.params)
        except ValidationError as e:
            raise HTTPBadRequest(e)

        try:
            diagram: Diagram = self.diagram_repo.edit(
                self.requested_diagram_id, changes
            )
        except exceptions.DiagramNotFoundError:
            raise HTTPNotFound()

        return {"diagram": diagram}

    @view_config(request_method="DELETE")
    def diagram_delete(self):
        try:
            self.diagram_repo.delete(self.requested_diagram_id)
        except exceptions.DiagramNotFoundError:
            raise HTTPNotFound()
        else:
            return Response(
                status=204, headers={"Hx-Redirect": self.request.route_url("diagrams")}
            )

    @view_config(request_method="GET")
    def diagram_get(self):
        """Redirect to the diagram editor view."""
        return HTTPSeeOther(
            location=self.request.route_url(
                "diagram_view_editor", diagram_id=self.requested_diagram_id
            )
        )
