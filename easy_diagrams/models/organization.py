from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy import Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .meta import Base

# Association table for organization-user relationship with owner flag
organization_user_association = Table(
    "organization_users",
    Base.metadata,
    Column(
        "organization_id",
        UUID(as_uuid=True),
        ForeignKey("organizations.id"),
        primary_key=True,
    ),
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True),
    Column("is_owner", Boolean, default=False, nullable=False),
    Column("created_at", DateTime, default=datetime.now),
)


class OrganizationTable(Base):
    """Organization model.

    Organization-User Lifecycle:
    - Organizations can have multiple users as members
    - Each organization must have at least one owner
    - Users can be added by email (creates user if doesn't exist)
    - Owners have full control over the organization
    - Deleting an organization removes all user associations
    - Organizations are isolated - users can only access organizations they belong to
    """

    __tablename__ = "organizations"

    #: Publicly exposable Organization ID
    id = Column(UUID(as_uuid=True), default=uuid4, primary_key=True)

    #: Organization name
    name = Column(String(256), nullable=False)

    #: When this organization was created
    created_at = Column(DateTime, default=datetime.now)

    #: When the organization data was updated last time
    updated_at = Column(DateTime, onupdate=datetime.now)

    #: Organization's users
    users = relationship(
        "User", secondary=organization_user_association, back_populates="organizations"
    )
