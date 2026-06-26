from easy_diagrams.services.organization_repo import OrganizationRepo


def test_logout_when_organization_not_selected(testapp, dbsession, user_factory):
    user = user_factory()
    org_repo = OrganizationRepo(user.id, dbsession)
    org_repo.create("Org 1")
    org_repo.create("Org 2")

    testapp.get(
        "/social_login/google",
        status=303,
        headers={"TEST_USER_EMAIL": user.email},
    )
    testapp.set_cookie("csrf_token", "dummy_csrf_token")

    res = testapp.get("/diagrams", status=303)
    assert res.location.endswith("/login")

    res = testapp.get("/diagrams", status=303)
    assert "login" in res.location


def test_select_organization_page_allowed_without_selection(
    testapp, dbsession, user_factory
):
    user = user_factory()
    org_repo = OrganizationRepo(user.id, dbsession)
    org_repo.create("Org 1")
    org_repo.create("Org 2")

    res = testapp.get(
        "/social_login/google",
        status=303,
        headers={"TEST_USER_EMAIL": user.email},
    )
    assert "select-organization" in res.location

    testapp.set_cookie("csrf_token", "dummy_csrf_token")
    testapp.get("/select-organization", status=200)
