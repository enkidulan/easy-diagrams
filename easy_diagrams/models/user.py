from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .meta import Base


class User(Base):
    """User model.

    User-Organization Lifecycle:
    - Users can belong to multiple organizations
    - When a user is added to an organization, they get access to that organization's resources
    - Users can be owners or regular members of organizations
    - Deleting a user removes them from all organizations
    - Users are automatically created when added to organizations by email if they don't exist
    """

    __tablename__ = "users"

    #: Publicly exposable User ID
    id = Column(UUID(as_uuid=True), default=uuid4, primary_key=True)

    #: User Email
    email = Column(String(256), nullable=True, unique=True)

    #: When this user was created
    created_at = Column(DateTime, default=datetime.now)

    #: When the user data was updated last time
    updated_at = Column(DateTime, onupdate=datetime.now)

    #: When this user was activated: email confirmed or first social login
    activated_at = Column(DateTime, nullable=True)

    #: Is this user user enabled. The support can disable the use in the case of suspected malicious activity.
    enabled = Column(Boolean(name="user_enabled_binary"), default=True)

    #: When this logged in the system last time. Information stored for the security audits.
    last_login_at = Column(DateTime, nullable=True)

    #: User's diagrams
    diagrams = relationship("DiagramTable", back_populates="user")

    #: User's folders
    folders = relationship("FolderTable", back_populates="user")

    #: User's organizations
    organizations = relationship(
        "OrganizationTable", secondary="organization_users", back_populates="users"
    )
