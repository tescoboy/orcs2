"""
UI test specific fixtures.

These fixtures are for testing the web interface.
"""

import os
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def ui_test_mode():
    """Enable UI test authentication mode."""
    os.environ["ADCP_AUTH_TEST_MODE"] = "true"

    yield

    # Cleanup
    del os.environ["ADCP_AUTH_TEST_MODE"]


@pytest.fixture
def test_users():
    """Provide test user credentials."""
    return {
        "super_admin": {"email": "test_super_admin@example.com", "password": "test123", "role": "super_admin"},
        "tenant_admin": {
            "email": "test_tenant_admin@example.com",
            "password": "test123",
            "role": "tenant_admin",
            "tenant_id": "test_tenant",
        },
        "tenant_user": {
            "email": "test_tenant_user@example.com",
            "password": "test123",
            "role": "tenant_user",
            "tenant_id": "test_tenant",
        },
    }


@pytest.fixture
def ui_client(ui_test_mode):
    """Provide Flask client configured for UI testing."""
    # Mock database before importing
    with patch("db_config.get_db_connection") as mock_db_conn:
        mock_db = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_cursor.fetchone.return_value = None
        mock_db.execute.return_value = mock_cursor
        mock_db_conn.return_value = mock_db

        # Mock GAM inventory service
        with patch("gam_inventory_service.get_db_connection", return_value=mock_db):
            from src.admin.app import create_app

            app, _ = create_app()
            app.config["TESTING"] = True
            app.config["SECRET_KEY"] = "test-secret-key"
            app.config["WTF_CSRF_ENABLED"] = False

            client = app.test_client()

            yield client


@pytest.fixture
def authenticated_ui_client(ui_client, test_users):
    """Provide authenticated UI client."""
    # Login as super admin
    response = ui_client.post(
        "/test/auth",
        json={"email": test_users["super_admin"]["email"], "password": test_users["super_admin"]["password"]},
    )

    assert response.status_code == 200

    yield ui_client


@pytest.fixture
def mock_javascript():
    """Mock JavaScript functionality for testing."""

    class MockJavaScript:
        def __init__(self):
            self.console_logs = []
            self.alerts = []
            self.confirms = []
            self.local_storage = {}

        def console_log(self, *args):
            self.console_logs.append(args)

        def alert(self, message):
            self.alerts.append(message)

        def confirm(self, message):
            self.confirms.append(message)
            return True  # Always confirm

        def set_local_storage(self, key, value):
            self.local_storage[key] = value

        def get_local_storage(self, key):
            return self.local_storage.get(key)

    return MockJavaScript()


@pytest.fixture
def form_data_builder():
    """Build form data for testing."""

    class FormDataBuilder:
        def __init__(self):
            self.data = {}

        def add_field(self, name, value):
            self.data[name] = value
            return self

        def add_file(self, name, filename, content):
            from io import BytesIO

            self.data[name] = (BytesIO(content), filename)
            return self

        def build(self):
            return self.data

    return FormDataBuilder()


@pytest.fixture
def page_validator():
    """Validate page content."""

    class PageValidator:
        def __init__(self, response):
            self.response = response
            self.content = response.data.decode("utf-8")

        def has_text(self, text):
            return text in self.content

        def has_element(self, selector):
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(self.content, "html.parser")
            return soup.select(selector) != []

        def get_form_action(self, form_id):
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(self.content, "html.parser")
            form = soup.find("form", id=form_id)
            return form.get("action") if form else None

        def get_links(self):
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(self.content, "html.parser")
            return [a.get("href") for a in soup.find_all("a")]

        def get_json(self):
            import json

            return json.loads(self.content)

    def _validator(response):
        return PageValidator(response)

    return _validator


@pytest.fixture
def mock_creative_parser():
    """Mock creative parsing service."""
    with patch("ai_creative_format_service.AICreativeFormatService") as mock_service:
        instance = MagicMock()
        instance.parse_creative.return_value = {
            "format": "display_300x250",
            "content": {"headline": "Test Ad", "body": "Test content", "image_url": "https://example.com/image.jpg"},
        }
        mock_service.return_value = instance

        yield instance


@pytest.fixture
def mock_file_upload():
    """Mock file upload handling."""

    def _create_file(filename, content, content_type="text/plain"):
        from io import BytesIO

        from werkzeug.datastructures import FileStorage

        return FileStorage(
            stream=BytesIO(content.encode() if isinstance(content, str) else content),
            filename=filename,
            content_type=content_type,
        )

    return _create_file
