import base64
from datetime import datetime
from typing import Annotated
from typing import NewType
from uuid import UUID

from pydantic import ConfigDict
from pydantic import StringConstraints
from pydantic.dataclasses import dataclass

# TODO: add design notes to Readme to why the frozen=True is used

DiagramID = NewType("DiagramID", str)  # TODO: limit len to 64


@dataclass(frozen=True, config=ConfigDict(extra="forbid"))
class DiagramRender:
    image: bytes
    version: int  # TODO: enforce proper versioning

    @property
    def image_base64(self):  # TODO: move to a presenter, remove from here
        return base64.b64encode(self.image).decode()


@dataclass(frozen=True, config=ConfigDict(extra="forbid"))
class Diagram:
    id: DiagramID
    user_id: UUID
    title: str | None
    is_public: bool
    code: str | None
    code_version: int | None = None
    render: DiagramRender | None = None


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

    @property
    def short_id(self):
        return self.id[:6]
