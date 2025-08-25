from easy_diagrams.models.organization import OrganizationTable
from easy_diagrams.services.organization_repo import OrganizationRepository


def test_create_for_user(dbsession):
    from easy_diagrams.models.user import User

    repo = OrganizationRepository(dbsession)
    user_email = "test@example.com"

    # Create user first
    user = User(email=user_email)
    dbsession.add(user)
    dbsession.flush()

    org_id = repo.create_for_user(user_email, user.id)

    # Check organization was created
    org = dbsession.query(OrganizationTable).filter_by(id=str(org_id)).one()
    assert org.name == f"{user_email}'s Organization"

    # Check user is owner
    from easy_diagrams.models.organization import organization_users

    result = dbsession.execute(
        organization_users.select().where(
            organization_users.c.organization_id == str(org_id),
            organization_users.c.user_id == user.id,
            organization_users.c.is_owner.is_(True),
        )
    ).fetchone()
    assert result is not None


def test_get_by_user(dbsession, user, organization):
    repo = OrganizationRepository(dbsession)

    org = repo.get_by_user(user.id)

    assert org.id == organization.id
    assert org.name is not None


def test_update_name(dbsession, user, organization):
    repo = OrganizationRepository(dbsession)
    new_name = "Updated Organization Name"

    repo.update_name(organization.id, new_name)

    org = dbsession.query(OrganizationTable).filter_by(id=organization.id).one()
    assert org.name == new_name
