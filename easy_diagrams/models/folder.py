import random
import string
from datetime import datetime

from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from .meta import Base


def _gen_folder_id() -> str:
    """Generate a unique identifier for the folder."""
    return "".join(random.choices(string.ascii_letters + string.digits, k=32))


class FolderTable(Base):
    """Folder model for organizing diagrams hierarchically."""

    __tablename__ = "folders"

    #: Unique publicly exposed identifier for the folder
    id = Column(String(32), default=_gen_folder_id, primary_key=True)

    #: Name of the folder
    name = Column(String(255), nullable=False, index=True)

    #: When this folder was created
    created_at = Column(DateTime, index=True, default=datetime.now)

    #: When the folder was updated last time
    updated_at = Column(
        DateTime, index=True, onupdate=datetime.now, default=datetime.now
    )

    #: Organization relationship
    organization_id = mapped_column(
        ForeignKey("organizations.id"), nullable=False, index=True
    )
    organization = relationship("OrganizationTable", back_populates="folders")

    #: Parent folder relationship (for nested folders)
    parent_id = mapped_column(ForeignKey("folders.id"), nullable=True, index=True)
    parent = relationship("FolderTable", remote_side=[id], back_populates="children")
    children = relationship("FolderTable", back_populates="parent")

    #: Diagrams in this folder
    diagrams = relationship("DiagramTable", back_populates="folder")
