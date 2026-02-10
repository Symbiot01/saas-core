"""
Custom exceptions for saas-core library.
"""


class SaasCoreError(Exception):
    """Base exception for all saas-core errors."""

    pass


class AuthenticationError(SaasCoreError):
    """Raised when JWT token verification fails.

    This can occur due to:
    - Invalid token signature
    - Expired token
    - Invalid issuer
    - Invalid audience
    - Missing required claims
    """

    pass


class EmailNotVerifiedError(AuthenticationError):
    """Raised when email verification is required but the token's email is not verified.

    This exception is raised when:
    - SAAS_CORE_REQUIRE_EMAIL_VERIFIED is True (default)
    - The token's email_verified claim is False
    """

    pass


class ConfigurationError(SaasCoreError):
    """Raised when there's a configuration error.

    This can occur due to:
    - Missing required environment variables
    - Invalid configuration values
    - Configuration validation failures
    """

    pass


class DatabaseError(SaasCoreError):
    """Raised when there's a database-related error.

    Note: Database functionality is currently a placeholder.
    This exception is defined for future use.
    """

    pass
