from dataclasses import dataclass

from pyramid.request import Request
from sqlalchemy import exc as sqlalchemy_exc

from easy_diagrams import interfaces
from easy_diagrams.domain.folder import Folder
from easy_diagrams.domain.folder import FolderEdit
from easy_diagrams.domain.folder import FolderID
from easy_diagrams.domain.folder import FolderListItem
from easy_diagrams.exceptions import DiagramNotFoundError
from easy_diagrams.models.folder import FolderTable


@dataclass
class FolderRepository:
    """Repository for folder operations."""

    organization_id: str
    dbsession: object

    def create(self, name: str, parent_id: FolderID = None) -> FolderID:
        folder = FolderTable(
            organization_id=self.organization_id, name=name, parent_id=parent_id
        )
        self.dbsession.add(folder)
        self.dbsession.flush()
        return FolderID(folder.id)

    def _get(self, folder_id: FolderID) -> FolderTable:
        try:
            folder = (
                self.dbsession.query(FolderTable)
                .filter_by(id=folder_id, organization_id=self.organization_id)
                .one()
            )
        except sqlalchemy_exc.NoResultFound:
            raise DiagramNotFoundError(f"Folder {folder_id} not found.")
        return folder

    def get(self, folder_id: FolderID) -> Folder:
        folder = self._get(folder_id)
        return Folder(
            id=FolderID(folder.id),
            organization_id=folder.organization_id,
            name=folder.name,
            parent_id=FolderID(folder.parent_id) if folder.parent_id else None,
        )

    def delete(self, folder_id: FolderID):
        folder = self._get(folder_id)
        self.dbsession.delete(folder)

    def list(
        self, parent_id: FolderID = None, offset: int = 0, limit: int = None
    ) -> list[FolderListItem]:
        query = self.dbsession.query(
            FolderTable.id,
            FolderTable.name,
            FolderTable.parent_id,
            FolderTable.created_at,
            FolderTable.updated_at,
        ).filter_by(organization_id=self.organization_id)

        if parent_id is not None:
            query = query.filter_by(parent_id=parent_id)
        else:
            query = query.filter(FolderTable.parent_id.is_(None))

        query = query.order_by(FolderTable.name)

        if limit is not None:
            query = query.offset(offset).limit(limit)

        return tuple(FolderListItem(**folder._asdict()) for folder in query.all())

    def count(self, parent_id: FolderID = None) -> int:
        query = self.dbsession.query(FolderTable).filter_by(
            organization_id=self.organization_id
        )

        if parent_id is not None:
            query = query.filter_by(parent_id=parent_id)
        else:
            query = query.filter(FolderTable.parent_id.is_(None))

        return query.count()

    def edit(self, folder_id: FolderID, changes: FolderEdit) -> Folder:
        folder = self._get(folder_id)
        if changes.name is not None:
            folder.name = changes.name
        if changes.parent_id is not None:
            folder.parent_id = changes.parent_id
        return self.get(folder_id)


def factory(context, request: Request):
    from easy_diagrams.models.organization import organization_users

    # Get user's organization_id from association table
    organization_id = None
    if request.authenticated_userid:
        result = (
            request.dbsession.query(organization_users.c.organization_id)
            .filter_by(user_id=request.authenticated_userid)
            .first()
        )
        organization_id = result.organization_id if result else None
    return FolderRepository(organization_id, request.dbsession)


def includeme(config):
    config.register_service_factory(factory, interfaces.IFolderRepo)
