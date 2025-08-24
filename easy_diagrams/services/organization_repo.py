from uuid import UUID

from sqlalchemy import and_
from sqlalchemy.orm import Session
from zope.interface import implementer

from easy_diagrams.domain.organization import Organization
from easy_diagrams.domain.organization import OrganizationEdit
from easy_diagrams.domain.organization import OrganizationID
from easy_diagrams.domain.organization import OrganizationListItem
from easy_diagrams.interfaces import IOrganizationRepo
from easy_diagrams.models.organization import OrganizationTable
from easy_diagrams.models.organization import organization_user_association
from easy_diagrams.models.user import User


@implementer(IOrganizationRepo)
class OrganizationRepo:
    """Organization repository implementation."""

    def __init__(self, user_id: str, dbsession: Session):
        self.user_id = UUID(user_id)
        self.dbsession = dbsession

    def create(self, name: str) -> OrganizationID:
        """Create new organization and return its ID."""
        org = OrganizationTable(name=name)
        self.dbsession.add(org)
        self.dbsession.flush()

        # Add creator as owner directly without validation
        self.dbsession.execute(
            organization_user_association.insert().values(
                organization_id=org.id, user_id=self.user_id, is_owner=True
            )
        )

        return OrganizationID(org.id)

    def get(self, organization_id: OrganizationID) -> Organization:
        """Get organization by its ID."""
        org = self._get_user_organization(organization_id.value)
        return Organization(id=OrganizationID(org.id), name=org.name)

    def delete(self, organization_id: OrganizationID) -> None:
        """Delete organization by its ID and remove all user associations."""
        org = self._get_user_organization(organization_id.value)

        # Remove all user associations first
        self.dbsession.execute(
            organization_user_association.delete().where(
                organization_user_association.c.organization_id == organization_id.value
            )
        )

        # Delete the organization
        self.dbsession.delete(org)

    def list(self, offset: int = 0, limit: int = 20) -> list[OrganizationListItem]:
        """List user's organizations with pagination."""
        orgs = (
            self.dbsession.query(OrganizationTable)
            .join(organization_user_association)
            .filter(organization_user_association.c.user_id == self.user_id)
            .offset(offset)
            .limit(limit)
            .all()
        )

        return [
            OrganizationListItem(id=OrganizationID(org.id), name=org.name)
            for org in orgs
        ]

    def edit(
        self, organization_id: OrganizationID, changes: OrganizationEdit
    ) -> Organization:
        """Edit organization by its ID."""
        org = self._get_user_organization(organization_id.value)

        if changes.name is not None:
            org.name = changes.name

        self.dbsession.flush()

        return Organization(id=OrganizationID(org.id), name=org.name)

    def add_user(
        self, organization_id: OrganizationID, email: str, is_owner: bool = False
    ) -> None:
        """Add user to organization by email. Creates user if doesn't exist."""
        # Verify organization exists and user has access
        self._get_user_organization(organization_id.value)

        # Find or create user by email
        user = self.dbsession.query(User).filter(User.email == email).first()
        if not user:
            user = User(email=email)
            self.dbsession.add(user)
            self.dbsession.flush()

        # Check if association already exists
        existing = (
            self.dbsession.query(organization_user_association)
            .filter(
                and_(
                    organization_user_association.c.organization_id
                    == organization_id.value,
                    organization_user_association.c.user_id == user.id,
                )
            )
            .first()
        )

        if existing:
            raise ValueError(f"User {email} is already in organization")

        # Add association
        self.dbsession.execute(
            organization_user_association.insert().values(
                organization_id=organization_id.value,
                user_id=user.id,
                is_owner=is_owner,
            )
        )

    def remove_user(self, organization_id: OrganizationID, user_id: str) -> None:
        """Remove user from organization."""
        # Verify organization exists and user has access
        self._get_user_organization(organization_id.value)

        self.dbsession.execute(
            organization_user_association.delete().where(
                and_(
                    organization_user_association.c.organization_id
                    == organization_id.value,
                    organization_user_association.c.user_id == UUID(user_id),
                )
            )
        )

    def make_owner(self, organization_id: OrganizationID, user_id: str) -> None:
        """Make user an owner of the organization."""
        # Verify organization exists and user has access
        self._get_user_organization(organization_id.value)

        self.dbsession.execute(
            organization_user_association.update()
            .where(
                and_(
                    organization_user_association.c.organization_id
                    == organization_id.value,
                    organization_user_association.c.user_id == UUID(user_id),
                )
            )
            .values(is_owner=True)
        )

    def remove_owner(self, organization_id: OrganizationID, user_id: str) -> None:
        """Remove user from owners. Fails if user is the only owner."""
        # Check if user is currently an owner
        owners = self.get_owners(organization_id)
        if user_id not in owners:
            raise ValueError(f"User {user_id} is not an owner")

        # Prevent removing the last owner
        if len(owners) <= 1:
            raise ValueError("Cannot remove the last owner from organization")

        self.dbsession.execute(
            organization_user_association.update()
            .where(
                and_(
                    organization_user_association.c.organization_id
                    == organization_id.value,
                    organization_user_association.c.user_id == UUID(user_id),
                )
            )
            .values(is_owner=False)
        )

    def get_owners(
        self, organization_id: OrganizationID, offset: int = 0, limit: int = 20
    ) -> "list[str]":
        """Get paginated list of owner user IDs for the organization."""
        # Verify organization exists and user has access
        self._get_user_organization(organization_id.value)

        owners = self.dbsession.execute(
            organization_user_association.select()
            .where(
                and_(
                    organization_user_association.c.organization_id
                    == organization_id.value,
                    organization_user_association.c.is_owner.is_(True),
                )
            )
            .offset(offset)
            .limit(limit)
        ).fetchall()

        return [str(owner.user_id) for owner in owners]

    def list_users(
        self, organization_id: OrganizationID, offset: int = 0, limit: int = 20
    ) -> "list[str]":
        """List users in an organization with pagination."""
        # Verify organization exists and user has access
        self._get_user_organization(organization_id.value)

        users = self.dbsession.execute(
            organization_user_association.select()
            .where(
                organization_user_association.c.organization_id == organization_id.value
            )
            .offset(offset)
            .limit(limit)
        ).fetchall()

        return [str(user.user_id) for user in users]

    def _get_user_organization(self, organization_id: UUID) -> OrganizationTable:
        """Get organization that user has access to."""
        org = (
            self.dbsession.query(OrganizationTable)
            .join(organization_user_association)
            .filter(
                and_(
                    OrganizationTable.id == organization_id,
                    organization_user_association.c.user_id == self.user_id,
                )
            )
            .first()
        )

        if not org:
            raise ValueError(
                f"Organization {organization_id} not found or access denied"
            )

        return org
