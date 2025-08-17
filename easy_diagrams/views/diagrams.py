import functools
from dataclasses import dataclass

from pydantic import ValidationError
from pyramid.httpexceptions import HTTPBadRequest
from pyramid.httpexceptions import HTTPSeeOther
from pyramid.request import Request
from pyramid.response import Response
from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.view import view_config
from pyramid.view import view_defaults

from easy_diagrams import interfaces
from easy_diagrams.domain.diagram import Diagram
from easy_diagrams.domain.diagram import DiagramEdit


@dataclass
class PageListing:
    items: list
    total: int
    limit: int
    offset: int
    current_page: int
    num_pages: int

    @property
    def has_next(self) -> bool:
        return self.current_page < self.num_pages

    @property
    def next_page(self) -> int | None:
        if self.has_next:
            return self.current_page + 1
        return None

    @property
    def has_previous(self) -> bool:
        return self.current_page > 1

    @property
    def previous_page(self) -> int | None:
        if self.has_previous:
            return self.current_page - 1
        return None


@dataclass
class DiagramsRepoViewMixin:

    request: Request

    @functools.cached_property
    def diagram_repo(self):
        return self.request.find_service(interfaces.IDiagramRepo)

    @functools.cached_property
    def folder_repo(self):
        return self.request.find_service(interfaces.IFolderRepo)


@view_defaults(route_name="diagrams")
class Diagrams(DiagramsRepoViewMixin):

    @view_config(
        request_method="POST",
    )
    def create_item(self):
        action = self.request.params.get("action")

        if action == "create_diagram":
            folder_id = self.request.params.get("folder_id") or None
            diagram_id = self.diagram_repo.create(folder_id=folder_id)
            return HTTPSeeOther(
                location=self.request.route_url(
                    "diagram_view_editor", diagram_id=diagram_id, _query={"new": "true"}
                )
            )
        elif action == "create_folder":
            name = self.request.params.get("name")
            parent_id = self.request.params.get("parent_id") or None
            if not name:
                raise HTTPBadRequest("Folder name is required")
            self.folder_repo.create(name=name, parent_id=parent_id)
            query_params = {"folder_id": parent_id} if parent_id else {}
            return HTTPSeeOther(
                location=self.request.route_url("diagrams", _query=query_params)
            )
        else:
            # Default behavior for backward compatibility
            folder_id = self.request.params.get("folder_id") or None
            diagram_id = self.diagram_repo.create(folder_id=folder_id)
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
        folder_id = self.request.params.get("folder_id") or None
        page = int(self.request.params.get("page", 1))
        limit = int(self.request.registry.settings.get("diagrams.page_size", 10))
        offset = (page - 1) * limit

        # Get folder and diagram counts
        folder_count = self.folder_repo.count(parent_id=folder_id)
        diagram_count = self.diagram_repo.count(folder_id=folder_id)
        total_items = folder_count + diagram_count

        # Calculate pagination for combined items
        num_pages = (total_items + limit - 1) // limit if total_items > 0 else 1

        # Determine what to show on current page
        folders = []
        diagrams = []

        if offset < folder_count:
            # Show folders (and possibly diagrams)
            folder_limit = min(limit, folder_count - offset)
            folders = self.folder_repo.list(
                parent_id=folder_id, offset=offset, limit=folder_limit
            )

            remaining_slots = limit - len(folders)
            if remaining_slots > 0:
                # Fill remaining slots with diagrams
                diagrams = self.diagram_repo.list(
                    offset=0, limit=remaining_slots, folder_id=folder_id
                )
        else:
            # Show only diagrams
            diagram_offset = offset - folder_count
            diagrams = self.diagram_repo.list(
                offset=diagram_offset, limit=limit, folder_id=folder_id
            )

        page_listing = PageListing(
            items=diagrams,
            total=total_items,
            limit=limit,
            offset=offset,
            current_page=page,
            num_pages=num_pages,
        )

        current_folder = None
        if folder_id:
            current_folder = self.folder_repo.get(folder_id)

        return {
            "page_listing": page_listing,
            "folders": folders,
            "current_folder": current_folder,
            "folder_id": folder_id,
        }


class DiagramResourceMixin(DiagramsRepoViewMixin):

    @property
    def requested_diagram_id(self):
        return self.request.matchdict.get("diagram_id")

    @property
    def diagram(self):
        return self.diagram_repo.get(self.requested_diagram_id)


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
        route_name="diagram_view_image_png",
        permission=NO_PERMISSION_REQUIRED,
    )
    def rendered_image_png(self):
        return self._rendered_image("png")

    @view_config(
        route_name="diagram_view_image_svg",
        permission=NO_PERMISSION_REQUIRED,
    )
    def rendered_image_svg(self):
        return self._rendered_image("svg")

    def _rendered_image(self, file_format: str):
        image = self.diagram_repo.get_image_render(self.requested_diagram_id)
        response = Response(body=image)
        response.content_type = f"image/{file_format}"
        # name = slugify(self.diagram.title or "image")
        name = "image"
        response.headers["Content-Disposition"] = f"filename={name}.{file_format}"
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
        diagram: Diagram = self.diagram_repo.edit(self.requested_diagram_id, changes)
        return {"diagram": diagram}

    @view_config(request_method="DELETE")
    def diagram_delete(self):
        self.diagram_repo.delete(self.requested_diagram_id)
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
