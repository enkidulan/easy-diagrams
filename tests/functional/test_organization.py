"""Test organization functionality."""


class TestOrganizationEdit:
    """Test organization edit functionality."""

    def test_organization_edit_get(self, testapp):
        """Test GET request to organization edit page."""
        testapp.login()

        # This should not raise AttributeError: 'Request' object has no attribute 'user'
        res = testapp.get("/organization/edit", status=200)
        assert "organization" in res.text.lower()

    def test_organization_edit_post(self, testapp):
        """Test POST request to update organization."""
        testapp.login()

        # This should not raise AttributeError: 'Request' object has no attribute 'user'
        res = testapp.post(
            "/organization/edit",
            params={"name": "Updated Organization Name"},
            headers={"X-CSRF-Token": testapp.get_csrf_token()},
            status=303,
        )

        # Should redirect back to organization edit page
        assert res.location.endswith("/organization/edit")

    def test_add_user_to_organization(self, testapp, dbsession):
        """Test adding a user to organization."""
        testapp.login()

        # Create a new user in the database
        from easy_diagrams.models.user import User

        new_user = User(email="testuser@example.com")
        dbsession.add(new_user)
        dbsession.flush()

        # Get initial page to see current users
        initial_res = testapp.get("/organization/edit")
        assert "testuser@example.com" not in initial_res.text

        # Add user to organization
        res = testapp.post(
            "/organization/edit",
            params={"action": "add_user", "email": "testuser@example.com"},
            headers={"X-CSRF-Token": testapp.get_csrf_token()},
            status=303,
        )

        # Should redirect back to organization edit page
        assert res.location.endswith("/organization/edit")

        # Follow redirect and check if user appears in table
        follow_res = testapp.get("/organization/edit")
        assert "testuser@example.com" in follow_res.text
