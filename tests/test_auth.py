"""
Comprehensive tests for the authentication module using Firebase Admin SDK.
"""

import os
from unittest.mock import patch, MagicMock

import pytest
import firebase_admin

from saas_core.auth import verify_user, _initialize_firebase
from saas_core.config import get_config, reset_config
from saas_core.exceptions import (
    AuthenticationError,
    EmailNotVerifiedError,
    ConfigurationError,
)


class TestConfiguration:
    """Tests for configuration handling."""

    def test_missing_credentials(self):
        """Test that missing Firebase credentials raises ConfigurationError."""
        with patch.dict(os.environ, {}, clear=True):
            reset_config()
            with pytest.raises(ConfigurationError) as exc_info:
                verify_user("dummy-token")
            error_msg = str(exc_info.value).lower()
            assert (
                "firebase_credentials_path" in error_msg
                or "google_project_id" in error_msg
                or "credentials" in error_msg
            )

    def test_firebase_initialization_with_credentials_path(self, mock_config):
        """Test Firebase initialization with credentials path."""
        with patch("firebase_admin.credentials.Certificate") as mock_cert:
            with patch("firebase_admin.initialize_app") as mock_init:
                mock_cert.return_value = MagicMock()
                _initialize_firebase()
                mock_cert.assert_called_once()
                mock_init.assert_called_once()

    def test_firebase_initialization_with_project_id(self, mock_config_project_id):
        """Test Firebase initialization with project ID."""
        with patch("firebase_admin.initialize_app") as mock_init:
            _initialize_firebase()
            mock_init.assert_called_once()
            # Check that projectId was passed
            call_args = mock_init.call_args
            assert "options" in call_args.kwargs
            assert call_args.kwargs["options"]["projectId"] == "test-project-12345"

    def test_firebase_initialization_already_initialized(self, mock_config):
        """Test that Firebase initialization is skipped if already initialized."""
        with patch("firebase_admin._apps", {"default": MagicMock()}):
            with patch("firebase_admin.initialize_app") as mock_init:
                _initialize_firebase()
                mock_init.assert_not_called()

    def test_email_verification_config(self, mock_firebase_credentials_path):
        """Test email verification configuration parsing."""
        test_cases = [
            ("True", True),
            ("true", True),
            ("1", True),
            ("yes", True),
            ("False", False),
            ("false", False),
            ("0", False),
            ("no", False),
        ]

        for value, expected in test_cases:
            env_vars = {
                "SAAS_CORE_FIREBASE_CREDENTIALS_PATH": mock_firebase_credentials_path,
                "SAAS_CORE_REQUIRE_EMAIL_VERIFIED": value,
            }
            with patch.dict(os.environ, env_vars, clear=False):
                reset_config()
                config = get_config()
                assert config.require_email_verified == expected


class TestTokenVerification:
    """Tests for Firebase ID token verification."""

    def test_verify_valid_token(self, mock_config, mock_firebase_decoded_token):
        """Test verification of a valid token."""
        with patch("firebase_admin.credentials.Certificate") as mock_cert:
            with patch("firebase_admin.initialize_app") as mock_init:
                with patch("firebase_admin.auth.verify_id_token") as mock_verify:
                    mock_verify.return_value = mock_firebase_decoded_token

                    user_info = verify_user("valid-token")
                    assert user_info["uid"] == "test-user-123"
                    assert user_info["email"] == "test@example.com"
                    assert user_info["email_verified"] is True
                    mock_verify.assert_called_once_with("valid-token")

    def test_verify_expired_token(self, mock_config):
        """Test that expired tokens are rejected."""
        from firebase_admin._token_gen import ExpiredIdTokenError
        
        with patch("firebase_admin.credentials.Certificate") as mock_cert:
            with patch("firebase_admin.initialize_app") as mock_init:
                with patch("firebase_admin.auth.verify_id_token") as mock_verify:
                    mock_verify.side_effect = ExpiredIdTokenError("Token expired", None)

                    with pytest.raises(AuthenticationError) as exc_info:
                        verify_user("expired-token")
                    assert "expired" in str(exc_info.value).lower()

    def test_verify_revoked_token(self, mock_config):
        """Test that revoked tokens are rejected."""
        from firebase_admin._token_gen import RevokedIdTokenError
        
        with patch("firebase_admin.credentials.Certificate") as mock_cert:
            with patch("firebase_admin.initialize_app") as mock_init:
                with patch("firebase_admin.auth.verify_id_token") as mock_verify:
                    mock_verify.side_effect = RevokedIdTokenError("Token revoked")

                    with pytest.raises(AuthenticationError) as exc_info:
                        verify_user("revoked-token")
                    assert "revoked" in str(exc_info.value).lower()

    def test_verify_invalid_token(self, mock_config):
        """Test that invalid tokens are rejected."""
        with patch("firebase_admin.credentials.Certificate") as mock_cert:
            with patch("firebase_admin.initialize_app") as mock_init:
                with patch("firebase_admin.auth.verify_id_token") as mock_verify:
                    mock_verify.side_effect = firebase_admin.exceptions.InvalidArgumentError(
                        "Invalid token", None
                    )

                    with pytest.raises(AuthenticationError) as exc_info:
                        verify_user("invalid-token")
                    assert "invalid" in str(exc_info.value).lower()

    def test_verify_certificate_fetch_error(self, mock_config):
        """Test handling of certificate fetch errors."""
        with patch("firebase_admin.auth.verify_id_token") as mock_verify:
            mock_verify.side_effect = firebase_admin.exceptions.CertificateFetchError(
                "Failed to fetch certificate"
            )

            with pytest.raises(AuthenticationError) as exc_info:
                verify_user("token")
            assert "certificate" in str(exc_info.value).lower()

    def test_verify_missing_uid(self, mock_config):
        """Test that tokens missing 'uid' claim are rejected."""
        with patch("firebase_admin.auth.verify_id_token") as mock_verify:
            mock_verify.return_value = {
                "email": "test@example.com",
                "email_verified": True,
            }

            with pytest.raises(AuthenticationError) as exc_info:
                verify_user("token")
            assert "uid" in str(exc_info.value).lower()

    def test_verify_unverified_email_required(self, mock_config, mock_firebase_decoded_token):
        """Test that unverified emails are rejected when required."""
        token_data = mock_firebase_decoded_token.copy()
        token_data["email_verified"] = False

        with patch("firebase_admin.auth.verify_id_token") as mock_verify:
            mock_verify.return_value = token_data

            with pytest.raises(EmailNotVerifiedError) as exc_info:
                verify_user("token")
            assert "email" in str(exc_info.value).lower()
            assert "verified" in str(exc_info.value).lower()

    def test_verify_unverified_email_allowed(
        self, mock_config_no_email_verification, mock_firebase_decoded_token
    ):
        """Test that unverified emails are allowed when not required."""
        token_data = mock_firebase_decoded_token.copy()
        token_data["email_verified"] = False

        with patch("firebase_admin.auth.verify_id_token") as mock_verify:
            mock_verify.return_value = token_data

            user_info = verify_user("token")
            assert user_info["email_verified"] is False

    def test_verify_empty_token(self, mock_config):
        """Test that empty tokens are rejected."""
        with pytest.raises(AuthenticationError) as exc_info:
            verify_user("")
        assert "non-empty string" in str(exc_info.value).lower()

    def test_verify_none_token(self, mock_config):
        """Test that None tokens are rejected."""
        with pytest.raises(AuthenticationError) as exc_info:
            verify_user(None)
        assert "non-empty string" in str(exc_info.value).lower()

    def test_verify_generic_exception(self, mock_config):
        """Test handling of generic Firebase Admin exceptions."""
        with patch("firebase_admin.auth.verify_id_token") as mock_verify:
            mock_verify.side_effect = Exception("Unexpected error")

            with pytest.raises(AuthenticationError) as exc_info:
                verify_user("token")
            assert "verification failed" in str(exc_info.value).lower()

    def test_verify_returns_auth_time(self, mock_config, mock_firebase_decoded_token):
        """Test that auth_time is included in the response."""
        with patch("firebase_admin.auth.verify_id_token") as mock_verify:
            mock_verify.return_value = mock_firebase_decoded_token

            user_info = verify_user("token")
            assert "auth_time" in user_info
            assert user_info["auth_time"] == 1234567890
