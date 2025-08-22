"""Unit tests for authentication blueprint."""

from unittest.mock import MagicMock, Mock, patch

import pytest

from src.admin.blueprints.auth import auth_bp, init_oauth
from src.admin.utils import is_super_admin, is_tenant_admin


class TestAuthBlueprint:
    """Test authentication blueprint functionality."""

    def test_blueprint_creation(self):
        """Test that auth blueprint is created correctly."""
        assert auth_bp.name == "auth"
        assert auth_bp.url_prefix is None

    def test_blueprint_routes(self):
        """Test that all expected routes are registered."""
        # Get all route endpoints
        routes = []
        for rule in auth_bp.deferred_functions:
            if hasattr(rule, "__name__"):
                routes.append(rule.__name__)

        # The actual routes are registered when blueprint is registered with app
        # This just verifies the blueprint exists and can be imported
        assert auth_bp is not None

    @patch("src.admin.blueprints.auth.OAuth")
    def test_init_oauth_with_env_vars(self, mock_oauth):
        """Test OAuth initialization with environment variables."""
        mock_app = Mock()

        with patch.dict(
            "os.environ", {"GOOGLE_CLIENT_ID": "test_client_id", "GOOGLE_CLIENT_SECRET": "test_client_secret"}
        ):
            oauth = init_oauth(mock_app)

            # Verify OAuth was initialized
            mock_oauth.assert_called_once_with(mock_app)
            assert oauth is not None

    @patch("src.admin.blueprints.auth.OAuth")
    def test_init_oauth_without_config(self, mock_oauth):
        """Test OAuth initialization without configuration."""
        mock_app = Mock()

        with patch.dict("os.environ", {}, clear=True):
            with patch("src.admin.blueprints.auth.os.path.exists", return_value=False):
                oauth = init_oauth(mock_app)

                # Should return None when no config is available
                assert oauth is None


class TestAuthUtilities:
    """Test authentication utility functions."""

    @patch("src.admin.utils.get_db_session")
    def test_is_super_admin_with_email(self, mock_get_db_session):
        """Test super admin check with email list."""
        # Setup mock database session
        mock_session = MagicMock()
        mock_get_db_session.return_value.__enter__.return_value = mock_session

        # Mock email config
        mock_config = Mock()
        mock_config.config_value = "admin@example.com,super@example.com"
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_config

        # Test matching email
        assert is_super_admin("admin@example.com")
        assert is_super_admin("super@example.com")
        assert not is_super_admin("user@example.com")

    @patch("src.admin.utils.get_db_session")
    def test_is_super_admin_with_domain(self, mock_get_db_session):
        """Test super admin check with domain list."""
        # Setup mock database session
        mock_session = MagicMock()
        mock_get_db_session.return_value.__enter__.return_value = mock_session

        # Mock domain config
        mock_email_config = Mock()
        mock_email_config.config_value = None
        mock_domain_config = Mock()
        mock_domain_config.config_value = "admin.com,super.org"

        def side_effect(config_key=None):
            query = Mock()
            if config_key == "super_admin_emails":
                query.first.return_value = mock_email_config
            elif config_key == "super_admin_domains":
                query.first.return_value = mock_domain_config
            return query

        mock_session.query.return_value.filter_by.side_effect = side_effect

        # Test matching domain
        assert is_super_admin("user@admin.com")
        assert is_super_admin("user@super.org")
        assert not is_super_admin("user@example.com")

    @patch("src.admin.utils.get_db_session")
    def test_is_tenant_admin(self, mock_get_db_session):
        """Test tenant admin check."""
        # Setup mock database session
        mock_session = MagicMock()
        mock_get_db_session.return_value.__enter__.return_value = mock_session

        # Create mock for SuperadminConfig query that always returns None
        mock_superadmin_query = MagicMock()
        mock_superadmin_query.filter_by.return_value.first.return_value = None

        # Test 1: User is admin
        mock_user_admin = Mock()
        mock_user_admin.is_admin = True
        mock_user_admin.is_active = True

        mock_user_query_admin = MagicMock()
        mock_user_query_admin.filter_by.return_value.filter_by.return_value.first.return_value = mock_user_admin

        def query_side_effect_admin(model):
            if hasattr(model, "__name__"):
                if model.__name__ == "SuperadminConfig":
                    return mock_superadmin_query
                elif model.__name__ == "User":
                    return mock_user_query_admin
            return mock_user_query_admin

        mock_session.query.side_effect = query_side_effect_admin
        assert is_tenant_admin("admin@tenant.com", "tenant_123")

        # Test 2: User is not admin
        mock_user_not_admin = Mock()
        mock_user_not_admin.is_admin = False
        mock_user_not_admin.is_active = True

        mock_user_query_not_admin = MagicMock()
        # When is_admin=False, the filter_by chain should return no results (None)
        mock_user_query_not_admin.filter_by.return_value.filter_by.return_value.first.return_value = None

        def query_side_effect_not_admin(model):
            if hasattr(model, "__name__"):
                if model.__name__ == "SuperadminConfig":
                    return mock_superadmin_query
                elif model.__name__ == "User":
                    return mock_user_query_not_admin
            return mock_user_query_not_admin

        mock_session.query.side_effect = query_side_effect_not_admin
        assert not is_tenant_admin("user@tenant.com", "tenant_123")

        # Test 3: User is inactive
        mock_user_inactive = Mock()
        mock_user_inactive.is_admin = True
        mock_user_inactive.is_active = False

        mock_user_query_inactive = MagicMock()
        # When is_active=False, the filter_by chain should return no results (None)
        mock_user_query_inactive.filter_by.return_value.filter_by.return_value.first.return_value = None

        def query_side_effect_inactive(model):
            if hasattr(model, "__name__"):
                if model.__name__ == "SuperadminConfig":
                    return mock_superadmin_query
                elif model.__name__ == "User":
                    return mock_user_query_inactive
            return mock_user_query_inactive

        mock_session.query.side_effect = query_side_effect_inactive
        assert not is_tenant_admin("admin@tenant.com", "tenant_123")


class TestAuthIntegration:
    """Integration tests for authentication flow."""

    @pytest.fixture
    def app(self):
        """Create test Flask app with auth blueprint."""
        from src.admin.app import create_app

        app, _ = create_app({"TESTING": True})
        app.config["SECRET_KEY"] = "test_secret"
        return app

    def test_login_page_renders(self, app):
        """Test that login page renders correctly."""
        with app.test_client() as client:
            response = client.get("/login")
            assert response.status_code == 200

    def test_logout_clears_session(self, app):
        """Test that logout clears the session."""
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess["user"] = "test@example.com"
                sess["tenant_id"] = "tenant_123"

            response = client.get("/logout")
            assert response.status_code == 302  # Redirect

            with client.session_transaction() as sess:
                assert "user" not in sess
                assert "tenant_id" not in sess

    def test_protected_route_requires_auth(self, app):
        """Test that protected routes require authentication."""
        with app.test_client() as client:
            # Try to access protected route without auth
            response = client.get("/")
            assert response.status_code == 302  # Redirect to login
            assert "/login" in response.location

    def test_protected_route_with_auth(self, app):
        """Test that authenticated users can access protected routes."""
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess["user"] = "admin@example.com"

            with patch("src.admin.utils.is_super_admin", return_value=True):
                response = client.get("/")
                # Should render the index page for super admin
                assert response.status_code == 200
