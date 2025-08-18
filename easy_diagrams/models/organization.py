from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy import Table
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .meta import Base

# Association table for organization users with owner property
organization_users = Table(
    "organization_users",
    Base.metadata,
    Column("organization_id", String, ForeignKey("organizations.id"), primary_key=True),
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True),
    Column("is_owner", Boolean, nullable=False, default=False),
)


class OrganizationTable(Base):
    __tablename__ = "organizations"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    users = relationship(
        "User", secondary=organization_users, back_populates="organizations"
    )
    diagrams = relationship("DiagramTable", back_populates="organization")
    folders = relationship("FolderTable", back_populates="organization")
