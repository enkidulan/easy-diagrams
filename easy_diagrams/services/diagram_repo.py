from dataclasses import dataclass

from pyramid.request import Request
from sqlalchemy import exc as sqlalchemy_exc

from easy_diagrams import interfaces
from easy_diagrams.domain.diagram import Diagram
from easy_diagrams.domain.diagram import DiagramEdit
from easy_diagrams.domain.diagram import DiagramID
from easy_diagrams.domain.diagram import DiagramListItem
from easy_diagrams.domain.diagram import DiagramRender
from easy_diagrams.exceptions import DiagramNotFoundError
from easy_diagrams.models.diagram import DiagramTable


@dataclass
class DiagramRepository:
    """Abstraction for the database operations on the Diagram model.

    Main goal is to separate the database layer from other layers and create
    a simple and single point of access to the database, so that we can easily
    test the database layer in isolation and use fake it in other layers.
    """

    user_id: str
    dbsession: object
    diagram_renderer: interfaces.IDiagramRenderer

    def create(self) -> DiagramID:
        diagram = DiagramTable(user_id=self.user_id)
        self.dbsession.add(diagram)
        self.dbsession.flush()
        return DiagramID(diagram.id)

    def _get(self, diagram_id) -> DiagramTable:
        try:
            diagram = (
                self.dbsession.query(DiagramTable)
                .filter_by(id=diagram_id, user_id=self.user_id)
                .one()
            )
        except sqlalchemy_exc.NoResultFound:
            raise DiagramNotFoundError(f"Diagram {diagram_id} not found.")
        return diagram

    def get(self, diagram_id) -> Diagram:
        diagram = self._get(diagram_id)
        return Diagram(
            id=DiagramID(diagram.id),
            user_id=diagram.user_id,
            title=diagram.title,
            is_public=diagram.is_public,
            code=diagram.code,
            code_version=diagram.code_version,
            render=(
                DiagramRender(image=diagram.image, version=diagram.image_version)
                if diagram.image
                else None
            ),
        )

    def delete(self, diagram_id):
        diagram = self._get(diagram_id)
        self.dbsession.delete(diagram)

    def list(self, offset=0, limit=100) -> list[DiagramListItem]:

        return tuple(
            DiagramListItem(**diagram._asdict())
            for diagram in self.dbsession.query(
                DiagramTable.id,
                DiagramTable.title,
                DiagramTable.is_public,
                DiagramTable.created_at,
                DiagramTable.updated_at,
            )
            .filter_by(user_id=self.user_id)
            .order_by(DiagramTable.updated_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

    def count(self) -> int:
        return (
            self.dbsession.query(DiagramTable).filter_by(user_id=self.user_id).count()
        )

    def edit(self, diagram_id, changes: DiagramEdit) -> None:
        diagram = self._get(diagram_id)
        if changes.title is not None:
            diagram.title = changes.title
        if changes.is_public is not None:
            diagram.is_public = changes.is_public
        if changes.code is not None:
            diagram.code = changes.code
            image = self.diagram_renderer.render(diagram)
            diagram.set_image(image, diagram.code_version)
        return self.get(diagram_id)

    def get_image_render(self, diagram_id) -> bytes:
        try:
            diagram = self.dbsession.query(DiagramTable).filter_by(id=diagram_id).one()
        except sqlalchemy_exc.NoResultFound:
            raise DiagramNotFoundError(f"Diagram {diagram_id} not found.")
        if diagram.user_id != self.user_id and not diagram.is_public:
            raise DiagramNotFoundError(f"Diagram {diagram_id} not found.")
        if not diagram.image:
            raise DiagramNotFoundError(f"Diagram {diagram_id} has no image.")
        return diagram.image


def factory(context, request: Request):
    diagram_renderer = request.find_service(interfaces.IDiagramRenderer)
    return DiagramRepository(
        request.authenticated_userid, request.dbsession, diagram_renderer
    )


def includeme(config):
    config.register_service_factory(factory, interfaces.IDiagramRepo)
