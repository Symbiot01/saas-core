"""
Pytest configuration and shared fixtures for saas-core tests.
"""

import os
import time
from typing import Dict
from unittest.mock import patch
from datetime import datetime, timedelta, timezone

import pytest
import jwt
from cryptography import x509
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID


@pytest.fixture
def mock_google_project_id():
    """Fixture providing a mock Google project ID."""
    return "test-project-12345"


@pytest.fixture
def mock_google_audience(mock_google_project_id):
    """Fixture providing a mock Google audience (defaults to project ID)."""
    return mock_google_project_id


@pytest.fixture
def mock_config(mock_google_project_id, mock_google_audience):
    """Fixture providing mock configuration environment variables."""
    env_vars = {
        "SAAS_CORE_GOOGLE_PROJECT_ID": mock_google_project_id,
        "SAAS_CORE_GOOGLE_AUDIENCE": mock_google_audience,
        "SAAS_CORE_REQUIRE_EMAIL_VERIFIED": "True",
        "SAAS_CORE_JWKS_CACHE_TTL": "3600",
        "SAAS_CORE_JWT_LEEWAY": "60",
    }
    with patch.dict(os.environ, env_vars, clear=False):
        yield env_vars


@pytest.fixture
def mock_config_no_email_verification(mock_google_project_id):
    """Fixture providing mock config with email verification disabled."""
    env_vars = {
        "SAAS_CORE_GOOGLE_PROJECT_ID": mock_google_project_id,
        "SAAS_CORE_REQUIRE_EMAIL_VERIFIED": "False",
    }
    with patch.dict(os.environ, env_vars, clear=False):
        yield env_vars


@pytest.fixture
def rsa_key_pair():
    """Fixture providing an RSA key pair for testing."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()

    # Serialize keys
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    return {
        "private_key": private_key,
        "public_key": public_key,
        "private_pem": private_pem.decode(),
        "public_pem": public_pem.decode(),
    }


@pytest.fixture
def mock_jwt_token(rsa_key_pair, mock_google_project_id):
    """Fixture providing a valid mock JWT token for testing."""

    def _create_token(
        uid: str = "test-user-123",
        email: str = "test@example.com",
        email_verified: bool = True,
        expired: bool = False,
        invalid_issuer: bool = False,
        invalid_audience: bool = False,
        missing_sub: bool = False,
        missing_email: bool = False,
    ):
        now = int(time.time())
        issuer = f"https://securetoken.google.com/{mock_google_project_id}"
        audience = mock_google_project_id

        if invalid_issuer:
            issuer = "https://invalid-issuer.com"
        if invalid_audience:
            audience = "invalid-audience"

        payload = {
            "sub": None if missing_sub else uid,
            "email": None if missing_email else email,
            "email_verified": email_verified,
            "iss": issuer,
            "aud": audience,
            "iat": now - 60,  # Issued 60 seconds ago
            "exp": now - 60 if expired else now + 3600,  # Expires in 1 hour (or already expired)
            "auth_time": now - 60,
        }

        # Remove None values
        payload = {k: v for k, v in payload.items() if v is not None}

        token = jwt.encode(
            payload,
            rsa_key_pair["private_key"],
            algorithm="RS256",
            headers={"kid": "test-key-id"},
        )

        return token

    return _create_token


@pytest.fixture
def mock_google_jwks_response(rsa_key_pair):
    """Fixture providing a mock Google JWKS endpoint response."""

    def _create_response():
        # Google's JWKS endpoint returns X.509 certificates
        # We need to create a certificate from the key pair for testing
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from datetime import datetime, timedelta

        # Create a self-signed certificate for testing
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Test"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Test Org"),
            x509.NameAttribute(NameOID.COMMON_NAME, "test-key-id"),
        ])

        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            rsa_key_pair["public_key"]
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.now(timezone.utc)
        ).not_valid_after(
            datetime.now(timezone.utc) + timedelta(days=365)
        ).sign(rsa_key_pair["private_key"], hashes.SHA256())

        # Return as PEM string (as Google's endpoint does)
        cert_pem = cert.public_bytes(serialization.Encoding.PEM).decode()
        return {
            "test-key-id": cert_pem,
        }

    return _create_response


@pytest.fixture(autouse=True)
def clear_key_cache():
    """Fixture to clear the key cache before each test."""
    from saas_core.auth import _key_cache
    from saas_core.config import reset_config

    _key_cache.clear()
    reset_config()
    yield
    _key_cache.clear()
    reset_config()