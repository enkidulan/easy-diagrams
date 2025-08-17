from typing import TYPE_CHECKING

from zope.interface import Interface

if TYPE_CHECKING:
    from easy_diagrams.domain.diagram import Diagram
    from easy_diagrams.domain.diagram import DiagramEdit
    from easy_diagrams.domain.diagram import DiagramID
    from easy_diagrams.domain.diagram import DiagramListItem
    from easy_diagrams.domain.folder import Folder
    from easy_diagrams.domain.folder import FolderEdit
    from easy_diagrams.domain.folder import FolderID
    from easy_diagrams.domain.folder import FolderListItem


class ISocialLoginProvider(Interface):
    """Interface for social login provider."""

    def login(provider_name, request, response) -> str | None:
        """Return user email as `string` or `None` if action wasn't successful.

        If error occurred, raise :class:`~easy_diagram.exceptions.SocialLoginError` exception.
        """


class IDiagramRenderer(Interface):
    """Interface for social login provider."""

    def render(diagram):
        """ "Render the provided diagram."""


class IDiagramRepo(Interface):
    """Interface for Diagram repository."""

    def __init__(user_id: str, dbsession: object, diagram_renderer: IDiagramRenderer):
        """Initialize repository with user_id, dbsession and diagram_renderer."""

    def create(folder_id: "FolderID" = None) -> "DiagramID":
        """Create new diagram and return its ID."""

    def get(diagram_id: "DiagramID") -> "Diagram":
        """Get diagram by its ID."""

    def delete(diagram_id: "DiagramID") -> None:
        """Delete diagram by its ID."""

    def list(
        offset: int, limit: int, folder_id: "FolderID" = None
    ) -> list["DiagramListItem"]:
        """Paginated diagrams list."""

    def edit(diagram_id: "DiagramID", changes: "DiagramEdit") -> None:
        """Edit diagram by its ID."""

    def get_image_render(diagram_id: "DiagramID") -> bytes:
        """Get diagram image render as bytes by its ID."""

    def count(folder_id: "FolderID" = None) -> int:
        """Get total count of diagrams."""


class IFolderRepo(Interface):
    """Interface for Folder repository."""

    def create(name: str, parent_id: "FolderID" = None) -> "FolderID":
        """Create new folder and return its ID."""

    def get(folder_id: "FolderID") -> "Folder":
        """Get folder by its ID."""

    def delete(folder_id: "FolderID") -> None:
        """Delete folder by its ID."""

    def list(parent_id: "FolderID" = None) -> list["FolderListItem"]:
        """List folders by parent ID."""

    def edit(folder_id: "FolderID", changes: "FolderEdit") -> "Folder":
        """Edit folder by its ID."""
