"""
Configuration module for saas-core using Pydantic.

This module handles all environment variable loading and validation
using Pydantic's BaseSettings.
"""

import os
from typing import ClassVar, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from saas_core.exceptions import ConfigurationError


class AuthConfig(BaseSettings):
    """Configuration for authentication module.

    All settings are loaded from environment variables prefixed with SAAS_CORE_.
    """

    # Google's JWKS endpoint for GCIP (not configurable, always the same)
    GOOGLE_JWKS_ENDPOINT: ClassVar[str] = "https://www.googleapis.com/robot/v1/metadata/x509/securetoken@system.gserviceaccount.com"

    model_config = SettingsConfigDict(
        env_prefix="SAAS_CORE_",
        case_sensitive=False,
        extra="ignore",
    )

    # Required settings
    # Environment variable: SAAS_CORE_GOOGLE_PROJECT_ID
    google_project_id: str = Field(
        ...,
        description="Google Cloud Identity Platform project ID",
    )

    # Optional settings with defaults
    # Environment variable: SAAS_CORE_GOOGLE_AUDIENCE
    google_audience: Optional[str] = Field(
        default=None,
        description="Custom audience for token validation (defaults to project_id)",
    )

    # Environment variable: SAAS_CORE_REQUIRE_EMAIL_VERIFIED
    require_email_verified: bool = Field(
        default=True,
        description="Require email verification (default: True)",
    )

    # Environment variable: SAAS_CORE_JWKS_CACHE_TTL
    jwks_cache_ttl: int = Field(
        default=3600,
        description="JWKS cache TTL in seconds (default: 3600)",
        ge=1,
    )

    # Environment variable: SAAS_CORE_JWT_LEEWAY
    jwt_leeway: int = Field(
        default=60,
        description="JWT clock skew tolerance in seconds (default: 60)",
        ge=0,
    )

    @field_validator("require_email_verified", mode="before")
    @classmethod
    def parse_boolean(cls, v):
        """Parse boolean from string."""
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "on")
        return bool(v)

    @property
    def audience(self) -> str:
        """Get audience, defaulting to project_id if not set."""
        return self.google_audience or self.google_project_id

    @property
    def issuer_url(self) -> str:
        """Get the issuer URL for GCIP."""
        return f"https://securetoken.google.com/{self.google_project_id}"

    def model_post_init(self, __context):
        """Validate configuration after initialization."""
        if not self.google_project_id:
            raise ConfigurationError(
                "SAAS_CORE_GOOGLE_PROJECT_ID environment variable is required"
            )


# Global config instance - will be initialized on first access
_config: Optional[AuthConfig] = None


def get_config() -> AuthConfig:
    """Get the global configuration instance.

    The configuration is loaded from environment variables on first access
    and cached for subsequent calls.

    Returns:
        AuthConfig: The configuration instance.

    Raises:
        ConfigurationError: If required configuration is missing or invalid.
    """
    global _config
    if _config is None:
        try:
            _config = AuthConfig()
        except Exception as e:
            raise ConfigurationError(
                f"Failed to load configuration: {str(e)}"
            ) from e
    return _config


def reset_config():
    """Reset the global configuration instance.

    Useful for testing or reloading configuration.
    """
    global _config
    _config = None
