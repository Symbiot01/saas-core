"""
Comprehensive tests for the authentication module.
"""

import os
import time
from unittest.mock import patch, MagicMock

import pytest
import httpx
import jwt

from saas_core.auth import verify_user, get_google_public_keys
from saas_core.config import get_config, reset_config
from saas_core.exceptions import (
    AuthenticationError,
    EmailNotVerifiedError,
    ConfigurationError,
)


class TestConfiguration:
    """Tests for configuration handling."""

    def test_missing_project_id(self):
        """Test that missing SAAS_CORE_GOOGLE_PROJECT_ID raises ConfigurationError."""
        with patch.dict(os.environ, {}, clear=True):
            reset_config()
            with pytest.raises(ConfigurationError) as exc_info:
                verify_user("dummy-token")
            # Check for any variation of the error message
            error_msg = str(exc_info.value).lower()
            assert (
                "google_project_id" in error_msg
                or "goog_project_id" in error_msg
                or "project_id" in error_msg
                or "required" in error_msg
            )

    def test_issuer_url_construction(self, mock_config):
        """Test issuer URL construction."""
        config = get_config()
        assert config.issuer_url == f"https://securetoken.google.com/{mock_config['SAAS_CORE_GOOGLE_PROJECT_ID']}"

    def test_custom_audience(self, mock_google_project_id):
        """Test that custom audience is used when provided."""
        custom_audience = "custom-audience-123"
        env_vars = {
            "SAAS_CORE_GOOGLE_PROJECT_ID": mock_google_project_id,
            "SAAS_CORE_GOOGLE_AUDIENCE": custom_audience,
        }
        with patch.dict(os.environ, env_vars, clear=False):
            reset_config()
            config = get_config()
            assert config.audience == custom_audience

    def test_email_verification_config(self, mock_google_project_id):
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
                "SAAS_CORE_GOOGLE_PROJECT_ID": mock_google_project_id,
                "SAAS_CORE_REQUIRE_EMAIL_VERIFIED": value,
            }
            with patch.dict(os.environ, env_vars, clear=False):
                reset_config()
                config = get_config()
                assert config.require_email_verified == expected


class TestGooglePublicKeys:
    """Tests for Google public key fetching and caching."""

    def test_fetch_public_keys_success(self, mock_config, mock_google_jwks_response):
        """Test successful fetching of public keys."""
        mock_response = mock_google_jwks_response()

        with patch("httpx.Client") as mock_client:
            mock_response_obj = MagicMock()
            mock_response_obj.json.return_value = mock_response
            mock_response_obj.raise_for_status.return_value = None
            mock_client_instance = MagicMock()
            mock_client_instance.__enter__.return_value.get.return_value = (
                mock_response_obj
            )
            mock_client.return_value = mock_client_instance

            keys = get_google_public_keys()
            assert isinstance(keys, dict)
            assert "test-key-id" in keys

    def test_fetch_public_keys_http_error(self, mock_config):
        """Test handling of HTTP errors when fetching keys."""
        with patch("httpx.Client") as mock_client:
            mock_client_instance = MagicMock()
            mock_client_instance.__enter__.return_value.get.side_effect = (
                httpx.HTTPError("Connection failed")
            )
            mock_client.return_value = mock_client_instance

            with pytest.raises(AuthenticationError) as exc_info:
                get_google_public_keys()
            assert "Failed to fetch Google public keys" in str(exc_info.value)

    def test_public_keys_caching(self, mock_config, mock_google_jwks_response):
        """Test that public keys are cached."""
        mock_response = mock_google_jwks_response()

        with patch("httpx.Client") as mock_client:
            mock_response_obj = MagicMock()
            mock_response_obj.json.return_value = mock_response
            mock_response_obj.raise_for_status.return_value = None
            mock_client_instance = MagicMock()
            mock_client_instance.__enter__.return_value.get.return_value = (
                mock_response_obj
            )
            mock_client.return_value = mock_client_instance

            # First call should fetch from API
            keys1 = get_google_public_keys()
            # Second call should use cache
            keys2 = get_google_public_keys()

            # Should only be called once due to caching
            assert mock_client_instance.__enter__.return_value.get.call_count == 1
            assert keys1 == keys2


class TestTokenVerification:
    """Tests for JWT token verification."""

    def test_verify_valid_token(
        self, mock_config, mock_jwt_token, mock_google_jwks_response, rsa_key_pair
    ):
        """Test verification of a valid token."""
        token = mock_jwt_token()
        mock_response = mock_google_jwks_response()

        with patch("httpx.Client") as mock_client:
            mock_response_obj = MagicMock()
            mock_response_obj.json.return_value = mock_response
            mock_response_obj.raise_for_status.return_value = None
            mock_client_instance = MagicMock()
            mock_client_instance.__enter__.return_value.get.return_value = (
                mock_response_obj
            )
            mock_client.return_value = mock_client_instance

            user_info = verify_user(token)
            assert user_info["uid"] == "test-user-123"
            assert user_info["email"] == "test@example.com"
            assert user_info["email_verified"] is True

    def test_verify_expired_token(
        self, mock_config, mock_jwt_token, mock_google_jwks_response, rsa_key_pair
    ):
        """Test that expired tokens are rejected."""
        token = mock_jwt_token(expired=True)
        mock_response = mock_google_jwks_response()

        with patch("httpx.Client") as mock_client:
            mock_response_obj = MagicMock()
            mock_response_obj.json.return_value = mock_response
            mock_response_obj.raise_for_status.return_value = None
            mock_client_instance = MagicMock()
            mock_client_instance.__enter__.return_value.get.return_value = (
                mock_response_obj
            )
            mock_client.return_value = mock_client_instance

            with pytest.raises(AuthenticationError) as exc_info:
                verify_user(token)
            assert "expired" in str(exc_info.value).lower()

    def test_verify_invalid_signature(
        self, mock_config, mock_jwt_token, mock_google_jwks_response, rsa_key_pair
    ):
        """Test that tokens with invalid signatures are rejected."""
        # Create token with one key but verify with different key
        from cryptography.hazmat.primitives.asymmetric import rsa

        different_private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048
        )

        now = int(time.time())
        payload = {
            "sub": "test-user",
            "email": "test@example.com",
            "email_verified": True,
            "iss": f"https://securetoken.google.com/{mock_config['SAAS_CORE_GOOGLE_PROJECT_ID']}",
            "aud": mock_config["SAAS_CORE_GOOGLE_PROJECT_ID"],
            "iat": now - 60,
            "exp": now + 3600,
        }

        token = jwt.encode(
            payload,
            different_private_key,
            algorithm="RS256",
            headers={"kid": "test-key-id"},
        )

        mock_response = mock_google_jwks_response()

        with patch("httpx.Client") as mock_client:
            mock_response_obj = MagicMock()
            mock_response_obj.json.return_value = mock_response
            mock_response_obj.raise_for_status.return_value = None
            mock_client_instance = MagicMock()
            mock_client_instance.__enter__.return_value.get.return_value = (
                mock_response_obj
            )
            mock_client.return_value = mock_client_instance

            with pytest.raises(AuthenticationError) as exc_info:
                verify_user(token)
            assert "signature" in str(exc_info.value).lower()

    def test_verify_invalid_issuer(
        self, mock_config, mock_jwt_token, mock_google_jwks_response, rsa_key_pair
    ):
        """Test that tokens with invalid issuer are rejected."""
        token = mock_jwt_token(invalid_issuer=True)
        mock_response = mock_google_jwks_response()

        with patch("httpx.Client") as mock_client:
            mock_response_obj = MagicMock()
            mock_response_obj.json.return_value = mock_response
            mock_response_obj.raise_for_status.return_value = None
            mock_client_instance = MagicMock()
            mock_client_instance.__enter__.return_value.get.return_value = (
                mock_response_obj
            )
            mock_client.return_value = mock_client_instance

            with pytest.raises(AuthenticationError) as exc_info:
                verify_user(token)
            assert "issuer" in str(exc_info.value).lower()

    def test_verify_invalid_audience(
        self, mock_config, mock_jwt_token, mock_google_jwks_response, rsa_key_pair
    ):
        """Test that tokens with invalid audience are rejected."""
        token = mock_jwt_token(invalid_audience=True)
        mock_response = mock_google_jwks_response()

        with patch("httpx.Client") as mock_client:
            mock_response_obj = MagicMock()
            mock_response_obj.json.return_value = mock_response
            mock_response_obj.raise_for_status.return_value = None
            mock_client_instance = MagicMock()
            mock_client_instance.__enter__.return_value.get.return_value = (
                mock_response_obj
            )
            mock_client.return_value = mock_client_instance

            with pytest.raises(AuthenticationError) as exc_info:
                verify_user(token)
            assert "audience" in str(exc_info.value).lower()

    def test_verify_missing_sub_claim(
        self, mock_config, mock_jwt_token, mock_google_jwks_response, rsa_key_pair
    ):
        """Test that tokens missing 'sub' claim are rejected."""
        token = mock_jwt_token(missing_sub=True)
        mock_response = mock_google_jwks_response()

        with patch("httpx.Client") as mock_client:
            mock_response_obj = MagicMock()
            mock_response_obj.json.return_value = mock_response
            mock_response_obj.raise_for_status.return_value = None
            mock_client_instance = MagicMock()
            mock_client_instance.__enter__.return_value.get.return_value = (
                mock_response_obj
            )
            mock_client.return_value = mock_client_instance

            with pytest.raises(AuthenticationError) as exc_info:
                verify_user(token)
            assert "sub" in str(exc_info.value).lower() or "subject" in str(
                exc_info.value
            ).lower()

    def test_verify_missing_email_claim(
        self, mock_config, mock_jwt_token, mock_google_jwks_response, rsa_key_pair
    ):
        """Test that tokens missing 'email' claim are rejected."""
        token = mock_jwt_token(missing_email=True)
        mock_response = mock_google_jwks_response()

        with patch("httpx.Client") as mock_client:
            mock_response_obj = MagicMock()
            mock_response_obj.json.return_value = mock_response
            mock_response_obj.raise_for_status.return_value = None
            mock_client_instance = MagicMock()
            mock_client_instance.__enter__.return_value.get.return_value = (
                mock_response_obj
            )
            mock_client.return_value = mock_client_instance

            with pytest.raises(AuthenticationError) as exc_info:
                verify_user(token)
            assert "email" in str(exc_info.value).lower()

    def test_verify_unverified_email_required(
        self, mock_config, mock_jwt_token, mock_google_jwks_response, rsa_key_pair
    ):
        """Test that unverified emails are rejected when required."""
        token = mock_jwt_token(email_verified=False)
        mock_response = mock_google_jwks_response()

        with patch("httpx.Client") as mock_client:
            mock_response_obj = MagicMock()
            mock_response_obj.json.return_value = mock_response
            mock_response_obj.raise_for_status.return_value = None
            mock_client_instance = MagicMock()
            mock_client_instance.__enter__.return_value.get.return_value = (
                mock_response_obj
            )
            mock_client.return_value = mock_client_instance

            with pytest.raises(EmailNotVerifiedError) as exc_info:
                verify_user(token)
            assert "email" in str(exc_info.value).lower()
            assert "verified" in str(exc_info.value).lower()

    def test_verify_unverified_email_allowed(
        self,
        mock_config_no_email_verification,
        mock_jwt_token,
        mock_google_jwks_response,
        rsa_key_pair,
    ):
        """Test that unverified emails are allowed when not required."""
        token = mock_jwt_token(email_verified=False)
        mock_response = mock_google_jwks_response()

        with patch("httpx.Client") as mock_client:
            mock_response_obj = MagicMock()
            mock_response_obj.json.return_value = mock_response
            mock_response_obj.raise_for_status.return_value = None
            mock_client_instance = MagicMock()
            mock_client_instance.__enter__.return_value.get.return_value = (
                mock_response_obj
            )
            mock_client.return_value = mock_client_instance

            user_info = verify_user(token)
            assert user_info["email_verified"] is False

    def test_verify_invalid_token_format(self, mock_config):
        """Test that invalid token formats are rejected."""
        with pytest.raises(AuthenticationError) as exc_info:
            verify_user("not.a.valid.jwt.token")
        assert "format" in str(exc_info.value).lower() or "invalid" in str(
            exc_info.value
        ).lower()

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

    def test_verify_missing_key_id(
        self, mock_config, mock_google_jwks_response, rsa_key_pair
    ):
        """Test handling of tokens with missing key ID in header."""
        # Create token without kid in header
        from cryptography.hazmat.primitives.asymmetric import rsa

        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

        now = int(time.time())
        payload = {
            "sub": "test-user",
            "email": "test@example.com",
            "email_verified": True,
            "iss": f"https://securetoken.google.com/{mock_config['SAAS_CORE_GOOGLE_PROJECT_ID']}",
            "aud": mock_config["SAAS_CORE_GOOGLE_PROJECT_ID"],
            "iat": now - 60,
            "exp": now + 3600,
        }

        token = jwt.encode(payload, private_key, algorithm="RS256", headers={})

        with pytest.raises(AuthenticationError) as exc_info:
            verify_user(token)
        assert "kid" in str(exc_info.value).lower() or "key id" in str(
            exc_info.value
        ).lower()
