"""
saas-core: Core authentication library for Hub & Spoke SaaS architecture.

This library provides JWT authentication verification via Google Cloud Identity Platform (GCIP).
It is designed to be consumed by all services in a microservices architecture for centralized
authentication.
"""

from saas_core.auth import verify_user, get_google_public_keys
from saas_core.exceptions import (
    AuthenticationError,
    EmailNotVerifiedError,
    ConfigurationError,
    DatabaseError,
)

__version__ = "0.1.0"
__all__ = [
    "verify_user",
    "get_google_public_keys",
    "AuthenticationError",
    "EmailNotVerifiedError",
    "ConfigurationError",
    "DatabaseError",
]
