"""
Authentication module using Firebase Admin SDK.

This module provides a simple wrapper around Firebase Admin SDK's
verify_id_token function for consistent token verification across services.
"""

import json
from typing import Dict, Optional

import firebase_admin
from firebase_admin import auth, credentials

from saas_core.config import get_config
from saas_core.exceptions import AuthenticationError, EmailNotVerifiedError, ConfigurationError

# Track if Firebase Admin has been initialized
_firebase_initialized = False


def _initialize_firebase():
    """Initialize Firebase Admin SDK (only once).

    Raises:
        ConfigurationError: If Firebase credentials are missing or invalid.
    """
    global _firebase_initialized

    if _firebase_initialized:
        return

    config = get_config()

    # Check if already initialized (e.g., by another library)
    if firebase_admin._apps:
        _firebase_initialized = True
        return

    try:
        if config.firebase_credentials_path:
            # Initialize with service account JSON file
            cred = credentials.Certificate(config.firebase_credentials_path)
            firebase_admin.initialize_app(cred)
        elif config.firebase_credentials_json:
            # Initialize with service account JSON from environment variable
            cred_dict = config.get_firebase_credentials_dict()
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        elif config.google_project_id:
            # Initialize with Application Default Credentials
            firebase_admin.initialize_app(
                options={"projectId": config.google_project_id}
            )
        else:
            raise ConfigurationError(
                "Firebase credentials not configured. Set one of: "
                "SAAS_CORE_FIREBASE_CREDENTIALS_PATH, "
                "SAAS_CORE_FIREBASE_CREDENTIALS_JSON, or "
                "SAAS_CORE_GOOGLE_PROJECT_ID"
            )

        _firebase_initialized = True

    except FileNotFoundError as e:
        raise ConfigurationError(
            f"Firebase credentials file not found: {config.firebase_credentials_path}"
        ) from e
    except json.JSONDecodeError as e:
        raise ConfigurationError(
            f"Invalid JSON in SAAS_CORE_FIREBASE_CREDENTIALS_JSON: {str(e)}"
        ) from e
    except Exception as e:
        raise ConfigurationError(
            f"Failed to initialize Firebase Admin SDK: {str(e)}"
        ) from e


def verify_user(token: str) -> Dict[str, any]:
    """Verify a Firebase ID token using Firebase Admin SDK.

    This is a wrapper around Firebase Admin SDK's verify_id_token that:
    - Handles Firebase initialization automatically
    - Provides consistent error handling
    - Checks email verification if required
    - Returns a standardized user info dictionary

    Args:
        token: Firebase ID token string (typically from Authorization header).

    Returns:
        Dictionary containing user information:
        {
            "uid": str,              # User ID
            "email": str,            # User email
            "email_verified": bool,  # Email verification status
            "auth_time": int,       # Authentication time (if available)
        }

    Raises:
        AuthenticationError: If token is invalid, expired, or verification fails.
        EmailNotVerifiedError: If email verification is required but not verified.
        ConfigurationError: If Firebase is not properly configured.

    Example:
        >>> token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
        >>> user_info = verify_user(token)
        >>> print(user_info["uid"])
        "user123"
    """
    if not token or not isinstance(token, str):
        raise AuthenticationError("Token must be a non-empty string")

    # Initialize Firebase Admin SDK (only happens once)
    _initialize_firebase()

    # Get configuration
    config = get_config()

    # Verify token using Firebase Admin SDK
    try:
        decoded_token = auth.verify_id_token(token)
    except firebase_admin.exceptions.InvalidArgumentError as e:
        raise AuthenticationError(f"Invalid token: {str(e)}")
    except firebase_admin.exceptions.ExpiredIdTokenError:
        raise AuthenticationError("Token has expired")
    except firebase_admin.exceptions.RevokedIdTokenError:
        raise AuthenticationError("Token has been revoked")
    except firebase_admin.exceptions.CertificateFetchError as e:
        raise AuthenticationError(f"Failed to fetch certificate: {str(e)}")
    except Exception as e:
        # Catch any other Firebase Admin errors
        raise AuthenticationError(f"Token verification failed: {str(e)}")

    # Extract user information
    uid = decoded_token.get("uid")
    email = decoded_token.get("email")
    email_verified = decoded_token.get("email_verified", False)
    auth_time = decoded_token.get("auth_time")

    if not uid:
        raise AuthenticationError("Token missing 'uid' claim")

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
