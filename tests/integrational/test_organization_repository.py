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
    from easy_diagrams.models.organization import organization_owners

    result = dbsession.execute(
        organization_owners.select().where(
            organization_owners.c.organization_id == str(org_id),
            organization_owners.c.user_id == user.id,
        )
    ).fetchone()
    assert result is not None


def test_get_by_user(dbsession, user):
    repo = OrganizationRepository(dbsession)

    org = repo.get_by_user(user.id)

    assert org.id == user.organization_id
    assert user.email in org.name


def test_update_name(dbsession, user):
    repo = OrganizationRepository(dbsession)
    new_name = "Updated Organization Name"

    repo.update_name(user.organization_id, new_name)

    org = dbsession.query(OrganizationTable).filter_by(id=user.organization_id).one()
    assert org.name == new_name
