from datetime import datetime
from typing import Annotated
from typing import NewType

from pydantic import ConfigDict
from pydantic import StringConstraints
from pydantic.dataclasses import dataclass

DiagramID = NewType("DiagramID", str)


@dataclass(frozen=True, config=ConfigDict(extra="forbid"))
class DiagramRender:
    image: bytes
    version: int


@dataclass(frozen=True, config=ConfigDict(extra="forbid"))
class Diagram:
    id: DiagramID
    organization_id: str
    title: str | None
    is_public: bool
    code: str | None
    code_version: int | None = None
    render: DiagramRender | None = None
    folder_id: str | None = None


@dataclass(frozen=True, config=ConfigDict(extra="forbid"))
class DiagramEdit:
    title: Annotated[str, StringConstraints(max_length=300)] | None = None
    is_public: bool | None = None
    # code has is 10K characters limit
    code: Annotated[str, StringConstraints(max_length=10_240)] | None = None


@dataclass(frozen=True, config=ConfigDict(extra="forbid"))
class DiagramListItem:
    id: DiagramID
    title: str | None
    is_public: bool
    updated_at: datetime
    created_at: datetime
    folder_id: str | None = None

    @property
    def short_id(self):
        return self.id[:6]
