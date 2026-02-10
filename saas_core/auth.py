"""
Authentication module for Google Cloud Identity Platform (GCIP) JWT verification.

This module provides stateless JWT token verification using Google's public keys
from the JWKS endpoint. It handles key caching, rotation, and comprehensive
claim validation.
"""

import time
from typing import Dict

import httpx
import jwt
from cryptography.hazmat.primitives import serialization
from cryptography import x509

from saas_core.config import get_config
from saas_core.exceptions import AuthenticationError, EmailNotVerifiedError

# In-memory cache for public keys
_key_cache: Dict[str, Dict] = {}


def get_google_public_keys() -> Dict[str, str]:
    """Fetch and cache Google's public keys from JWKS endpoint.

    Returns:
        Dictionary mapping key_id (kid) to PEM-encoded public key string.

    Raises:
        AuthenticationError: If keys cannot be fetched.
    """
    config = get_config()
    cache_key = "google_public_keys"
    cache_ttl = config.jwks_cache_ttl

    # Check cache
    if cache_key in _key_cache:
        cached_data = _key_cache[cache_key]
        if time.time() - cached_data["timestamp"] < cache_ttl:
            return cached_data["keys"]

    # Fetch keys from Google
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(config.GOOGLE_JWKS_ENDPOINT)
            response.raise_for_status()
            certs_dict = response.json()
    except httpx.HTTPError as e:
        raise AuthenticationError(f"Failed to fetch Google public keys: {str(e)}")

    # Convert X.509 certificates to RSA public keys
    public_keys = {}
    for key_id, cert_pem in certs_dict.items():
        try:
            # Load the X.509 certificate
            cert = x509.load_pem_x509_certificate(cert_pem.encode())
            # Extract the public key
            public_key = cert.public_key()
            # Serialize to PEM format
            pem_key = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
            public_keys[key_id] = pem_key.decode()
        except Exception as e:
            # Skip invalid keys but log the error
            continue

    # Update cache
    _key_cache[cache_key] = {
        "keys": public_keys,
        "timestamp": time.time(),
    }

    return public_keys


def _decode_token_header(token: str) -> Dict:
    """Extract and decode the JWT header without verification.

    Args:
        token: JWT token string.

    Returns:
        Decoded header dictionary.

    Raises:
        AuthenticationError: If token header is invalid.
    """
    try:
        header = jwt.get_unverified_header(token)
        return header
    except jwt.DecodeError as e:
        raise AuthenticationError(f"Invalid token format: {str(e)}")


def _get_verification_options(config) -> Dict:
    """Build PyJWT verification options.

    Args:
        config: AuthConfig instance.

    Returns:
        Dictionary of verification options for PyJWT.
    """
    return {
        "verify_signature": True,
        "verify_exp": True,
        "verify_iss": True,
        "verify_aud": True,
        "verify_iat": True,
        "verify_nbf": True,
        "issuer": config.issuer_url,
        "audience": config.audience,
        "algorithms": ["RS256"],
        "leeway": config.jwt_leeway,
    }


def verify_user(token: str) -> Dict[str, any]:
    """Verify a JWT token from Google Cloud Identity Platform.

    This function performs comprehensive token verification:
    - Fetches and caches Google's public keys
    - Verifies JWT signature using RS256
    - Validates all standard claims (iss, aud, exp, iat, nbf)
    - Checks email verification status (if required)
    - Extracts user identity information

    Args:
        token: JWT token string (typically from Authorization header).

    Returns:
        Dictionary containing user information:
        {
            "uid": str,              # User ID from 'sub' claim
            "email": str,            # User email
            "email_verified": bool,  # Email verification status
            "auth_time": int,       # Authentication time (if available)
        }

    Raises:
        AuthenticationError: If token is invalid, expired, or verification fails.
        EmailNotVerifiedError: If email verification is required but not verified.
        ConfigurationError: If configuration is missing or invalid.

    Example:
        >>> token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
        >>> user_info = verify_user(token)
        >>> print(user_info["uid"])
        "user123"
    """
    if not token or not isinstance(token, str):
        raise AuthenticationError("Token must be a non-empty string")

    # Get configuration
    config = get_config()

    # Decode header to get key ID
    header = _decode_token_header(token)
    key_id = header.get("kid")

    if not key_id:
        raise AuthenticationError("Token header missing 'kid' (key ID)")

    # Get public keys
    public_keys = get_google_public_keys()

    if key_id not in public_keys:
        # Key might have rotated, try refreshing cache
        _key_cache.clear()
        public_keys = get_google_public_keys()

        if key_id not in public_keys:
            raise AuthenticationError(
                f"Public key with ID '{key_id}' not found in Google's JWKS"
            )

    # Get verification options
    verification_options = _get_verification_options(config)

    # Verify and decode token
    try:
        decoded_token = jwt.decode(
            token,
            public_keys[key_id],
            **verification_options,
        )
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token has expired")
    except jwt.InvalidIssuerError:
        raise AuthenticationError("Token issuer is invalid")
    except jwt.InvalidAudienceError:
        raise AuthenticationError("Token audience is invalid")
    except jwt.InvalidSignatureError:
        raise AuthenticationError("Token signature is invalid")
    except jwt.InvalidTokenError as e:
        raise AuthenticationError(f"Token validation failed: {str(e)}")

    # Extract user information
    uid = decoded_token.get("sub")
    email = decoded_token.get("email")
    email_verified = decoded_token.get("email_verified", False)
    auth_time = decoded_token.get("auth_time")

    if not uid:
        raise AuthenticationError("Token missing 'sub' (subject/user_id) claim")

    if not email:
        raise AuthenticationError("Token missing 'email' claim")

    # Check email verification if required
    if config.require_email_verified and not email_verified:
        raise EmailNotVerifiedError(
            "Email verification is required but email is not verified"
        )

    return {
        "uid": uid,
        "email": email,
        "email_verified": email_verified,
        "auth_time": auth_time,
    }
