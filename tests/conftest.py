"""
Pytest configuration and shared fixtures for saas-core tests.
"""

import os
from unittest.mock import patch

import pytest


@pytest.fixture
def mock_firebase_credentials_path():
    """Fixture providing a mock Firebase credentials path."""
    return "/path/to/serviceAccountKey.json"


@pytest.fixture
def mock_google_project_id():
    """Fixture providing a mock Google project ID."""
    return "test-project-12345"


@pytest.fixture
def mock_config(mock_firebase_credentials_path):
    """Fixture providing mock configuration environment variables."""
    env_vars = {
        "SAAS_CORE_FIREBASE_CREDENTIALS_PATH": mock_firebase_credentials_path,
        "SAAS_CORE_REQUIRE_EMAIL_VERIFIED": "True",
    }
    with patch.dict(os.environ, env_vars, clear=False):
        yield env_vars


@pytest.fixture
def mock_config_project_id(mock_google_project_id):
    """Fixture providing mock config using project ID instead of credentials path."""
    env_vars = {
        "SAAS_CORE_GOOGLE_PROJECT_ID": mock_google_project_id,
        "SAAS_CORE_REQUIRE_EMAIL_VERIFIED": "True",
    }
    with patch.dict(os.environ, env_vars, clear=False):
        yield env_vars


@pytest.fixture
def mock_config_no_email_verification(mock_firebase_credentials_path):
    """Fixture providing mock config with email verification disabled."""
    env_vars = {
        "SAAS_CORE_FIREBASE_CREDENTIALS_PATH": mock_firebase_credentials_path,
        "SAAS_CORE_REQUIRE_EMAIL_VERIFIED": "False",
    }
    with patch.dict(os.environ, env_vars, clear=False):
        yield env_vars


@pytest.fixture
def mock_firebase_decoded_token():
    """Fixture providing a mock decoded Firebase token."""
    return {
        "uid": "test-user-123",
        "email": "test@example.com",
        "email_verified": True,
        "auth_time": 1234567890,
        "iss": "https://securetoken.google.com/test-project-12345",
        "aud": "test-project-12345",
        "iat": 1234567890,
        "exp": 1234571490,
    }


@pytest.fixture(autouse=True)
def reset_firebase_and_config():
    """Fixture to reset Firebase initialization and config before/after each test."""
    from saas_core.config import reset_config
    import firebase_admin
    import saas_core.auth

    # Reset before test
    reset_config()
    # Clear Firebase apps if initialized
    apps_to_delete = list(firebase_admin._apps.values())
    for app in apps_to_delete:
        try:
            firebase_admin.delete_app(app)
        except Exception:
            pass
    # Reset the initialization flag
    saas_core.auth._firebase_initialized = False

    yield

    # Reset after test
    reset_config()
    apps_to_delete = list(firebase_admin._apps.values())
    for app in apps_to_delete:
        try:
            firebase_admin.delete_app(app)
        except Exception:
            pass
    saas_core.auth._firebase_initialized = False
