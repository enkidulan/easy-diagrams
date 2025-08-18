from dataclasses import dataclass
from datetime import datetime
from typing import NewType

OrganizationID = NewType("OrganizationID", str)


@dataclass
class Organization:
    id: OrganizationID
    name: str
    created_at: datetime
    updated_at: datetime


@dataclass
class OrganizationListItem:
    id: OrganizationID
    name: str
    created_at: datetime
    updated_at: datetime


@dataclass
class OrganizationEdit:
    name: str | None = None
