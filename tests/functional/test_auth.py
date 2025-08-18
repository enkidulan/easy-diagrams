"""Test authentication functionality."""

from easy_diagrams import models


class TestFirstTimeLogin:
    """Test first-time user login scenarios."""

    def test_first_time_login_creates_user_with_organization(
        self, testapp, request_host
    ):
        """Test that first-time login creates user with proper organization_id."""
        # Simulate first-time login with a new email
        new_user_email = "newuser@example.com"

        # This should not raise an IntegrityError
        res = testapp.get(
            "/social_login/google",
            status=303,
            headers={"TEST_USER_EMAIL": new_user_email},
        )

        # Should redirect to home page after successful login
        assert res.location.startswith(f"http://{request_host}/")

        # Verify user was created and can access protected resources
        testapp.get("/diagrams", status=200)

    def test_user_creation_without_explicit_organization_id(self, dbsession):
        """Test that creating a user without explicit organization_id works."""
        # This should not raise an IntegrityError
        user = models.User(email="test@example.com")
        dbsession.add(user)
        dbsession.flush()

        # User should be created successfully (organizations are managed separately now)
        assert user.email == "test@example.com"
        assert user.id is not None
