"""
Configuration module for saas-core using Pydantic.

This module handles all environment variable loading and validation
using Pydantic's BaseSettings.
"""

import json
import os
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from saas_core.exceptions import ConfigurationError


class AuthConfig(BaseSettings):
    """Configuration for authentication module.

    All settings are loaded from environment variables prefixed with SAAS_CORE_.
    """

    model_config = SettingsConfigDict(
        env_prefix="SAAS_CORE_",
        case_sensitive=False,
        extra="ignore",
    )

    # Option 1: Path to Firebase service account JSON file
    # Environment variable: SAAS_CORE_FIREBASE_CREDENTIALS_PATH
    firebase_credentials_path: Optional[str] = Field(
        default=None,
        description="Path to Firebase service account JSON file",
    )

    # Option 2: Firebase service account JSON as string
    # Environment variable: SAAS_CORE_FIREBASE_CREDENTIALS_JSON
    firebase_credentials_json: Optional[str] = Field(
        default=None,
        description="Firebase service account JSON as string (alternative to file path)",
    )

    # Option 3: Firebase project ID (if using Application Default Credentials)
    # Environment variable: SAAS_CORE_GOOGLE_PROJECT_ID
    google_project_id: Optional[str] = Field(
        default=None,
        description="Google Cloud project ID (for Application Default Credentials)",
    )

    # Optional settings with defaults
    # Environment variable: SAAS_CORE_REQUIRE_EMAIL_VERIFIED
    require_email_verified: bool = Field(
        default=True,
        description="Require email verification (default: True)",
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

    @field_validator("firebase_credentials_json", mode="before")
    @classmethod
    def parse_json_string(cls, v):
        """Parse JSON string if provided."""
        if v is None or isinstance(v, dict):
            return v
        if isinstance(v, str):
            # Try to parse as JSON to validate it
            try:
                json.loads(v)
            except json.JSONDecodeError:
                raise ValueError("SAAS_CORE_FIREBASE_CREDENTIALS_JSON must be valid JSON")
            return v
        return v

    def model_post_init(self, __context):
        """Validate configuration after initialization."""
        if not self.firebase_credentials_path and not self.firebase_credentials_json and not self.google_project_id:
            raise ConfigurationError(
                "One of the following must be set: "
                "SAAS_CORE_FIREBASE_CREDENTIALS_PATH, "
                "SAAS_CORE_FIREBASE_CREDENTIALS_JSON, or "
                "SAAS_CORE_GOOGLE_PROJECT_ID"
            )

    def get_firebase_credentials_dict(self) -> Optional[dict]:
        """Get Firebase credentials as a dictionary.
        
        Returns:
            dict if credentials_json is set, None otherwise.
        """
        if self.firebase_credentials_json:
            return json.loads(self.firebase_credentials_json)
        return None


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
