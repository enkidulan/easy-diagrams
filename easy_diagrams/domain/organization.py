from dataclasses import dataclass
from uuid import UUID


@dataclass
class OrganizationID:
    """Organization ID value object."""

    value: UUID


@dataclass
class Organization:
    """Organization domain model."""

    id: OrganizationID
    name: str


@dataclass
class OrganizationEdit:
    """Organization edit data."""

    name: str | None = None


@dataclass
class OrganizationListItem:
    """Organization list item."""

    id: OrganizationID
    name: str
