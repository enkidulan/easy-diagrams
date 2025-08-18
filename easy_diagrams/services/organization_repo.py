from dataclasses import dataclass
from typing import List
from uuid import uuid4

from pyramid.request import Request
from sqlalchemy import exc as sqlalchemy_exc

from easy_diagrams import interfaces
from easy_diagrams.domain.organization import Organization
from easy_diagrams.domain.organization import OrganizationID
from easy_diagrams.domain.organization import OrganizationListItem
from easy_diagrams.exceptions import DiagramNotFoundError
from easy_diagrams.models.organization import OrganizationTable
from easy_diagrams.models.organization import organization_users
from easy_diagrams.models.user import User


@dataclass
class OrganizationRepository:
    """Repository for organization operations."""

    dbsession: object

    def get(self, organization_id: OrganizationID) -> Organization:
        try:
            org = (
                self.dbsession.query(OrganizationTable)
                .filter_by(id=organization_id)
                .one()
            )
        except sqlalchemy_exc.NoResultFound:
            raise DiagramNotFoundError(f"Organization {organization_id} not found.")
        return Organization(
            id=OrganizationID(org.id),
            name=org.name,
            created_at=org.created_at,
            updated_at=org.updated_at,
        )

    def list(self) -> List[OrganizationListItem]:
        return tuple(
            OrganizationListItem(
                id=OrganizationID(org.id),
                name=org.name,
                created_at=org.created_at,
                updated_at=org.updated_at,
            )
            for org in self.dbsession.query(OrganizationTable)
            .order_by(OrganizationTable.name)
            .all()
        )

    def get_by_user(self, user_id) -> Organization:
        # Get organization through the association table
        result = (
            self.dbsession.query(organization_users.c.organization_id)
            .filter_by(user_id=user_id)
            .first()
        )
        if not result:
            raise DiagramNotFoundError(f"User {user_id} not in any organization.")
        return self.get(result.organization_id)

    def update_name(self, organization_id: OrganizationID, name: str):
        org = (
            self.dbsession.query(OrganizationTable).filter_by(id=organization_id).one()
        )
        org.name = name
        self.dbsession.flush()

    def get_user_organization_id(self, user_id) -> OrganizationID:
        """Get the organization ID for a user."""
        result = (
            self.dbsession.query(organization_users.c.organization_id)
            .filter_by(user_id=user_id)
            .first()
        )
        if not result:
            raise DiagramNotFoundError(f"User {user_id} not in any organization.")
        return OrganizationID(result.organization_id)

    def create_for_user(self, user_email: str, user_id) -> OrganizationID:
        org_id = str(uuid4())
        org = OrganizationTable(id=org_id, name=f"{user_email}'s Organization")
        self.dbsession.add(org)
        self.dbsession.flush()

        # Add user as owner
        self.dbsession.execute(
            organization_users.insert().values(
                organization_id=org_id, user_id=user_id, is_owner=True
            )
        )
        return OrganizationID(org_id)

    def get_users(self, organization_id: OrganizationID) -> List[User]:
        return (
            self.dbsession.query(User)
            .join(organization_users, User.id == organization_users.c.user_id)
            .filter(organization_users.c.organization_id == organization_id)
            .all()
        )

    def get_owners(self, organization_id: OrganizationID) -> List[User]:
        return (
            self.dbsession.query(User)
            .join(organization_users, User.id == organization_users.c.user_id)
            .filter(
                organization_users.c.organization_id == organization_id,
                organization_users.c.is_owner == True,  # noqa
            )
            .all()
        )

    def add_owner(self, organization_id: OrganizationID, email: str):
        # Find user in the organization
        user = (
            self.dbsession.query(User)
            .join(organization_users, User.id == organization_users.c.user_id)
            .filter(
                User.email == email,
                organization_users.c.organization_id == organization_id,
            )
            .first()
        )
        if user:
            # Update to make them owner
            self.dbsession.execute(
                organization_users.update()
                .where(
                    organization_users.c.organization_id == organization_id,
                    organization_users.c.user_id == user.id,
                )
                .values(is_owner=True)
            )

    def remove_owner(self, organization_id: OrganizationID, owner_id: str):
        self.dbsession.execute(
            organization_users.update()
            .where(
                organization_users.c.organization_id == organization_id,
                organization_users.c.user_id == owner_id,
            )
            .values(is_owner=False)
        )

    def add_user(self, organization_id: OrganizationID, email: str):
        # Find user by email
        user = self.dbsession.query(User).filter_by(email=email).first()
        if user:
            # Check if user is already in organization
            existing = (
                self.dbsession.query(organization_users)
                .filter_by(organization_id=organization_id, user_id=user.id)
                .first()
            )
            if not existing:
                # Add user to organization as regular member
                self.dbsession.execute(
                    organization_users.insert().values(
                        organization_id=organization_id, user_id=user.id, is_owner=False
                    )
                )
                self.dbsession.flush()


def factory(context, request: Request):
    return OrganizationRepository(request.dbsession)


def includeme(config):
    config.register_service_factory(factory, interfaces.IOrganizationRepo)
