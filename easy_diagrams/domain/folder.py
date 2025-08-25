from datetime import datetime
from typing import NewType
from uuid import UUID

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

FolderID = NewType("FolderID", str)


@dataclass(frozen=True, config=ConfigDict(extra="forbid"))
class Folder:
    id: FolderID
    organization_id: UUID
    name: str
    parent_id: FolderID | None = None


@dataclass(frozen=True, config=ConfigDict(extra="forbid"))
class FolderListItem:
    id: FolderID
    name: str
    parent_id: FolderID | None
    updated_at: datetime
    created_at: datetime

    @property
    def short_id(self):
        return self.id[:6]


@dataclass(frozen=True, config=ConfigDict(extra="forbid"))
class FolderEdit:
    name: str | None = None
    parent_id: FolderID | None = None
