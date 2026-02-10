"""
Placeholder tests for the database module.

Note: Database functionality is not yet implemented, so these tests
verify that placeholder functions raise NotImplementedError as expected.
"""

import pytest

from saas_core.database import get_db, init_db, close_db, DatabaseConfig
from saas_core.exceptions import DatabaseError


class TestDatabasePlaceholder:
    """Tests for database module placeholders."""

    def test_get_db_raises_not_implemented(self):
        """Test that get_db raises NotImplementedError."""
        with pytest.raises(NotImplementedError) as exc_info:
            get_db()
        assert "not yet implemented" in str(exc_info.value).lower()

    def test_init_db_raises_not_implemented(self):
        """Test that init_db raises NotImplementedError."""
        with pytest.raises(NotImplementedError) as exc_info:
            init_db()
        assert "not yet implemented" in str(exc_info.value).lower()

    def test_close_db_raises_not_implemented(self):
        """Test that close_db raises NotImplementedError."""
        with pytest.raises(NotImplementedError) as exc_info:
            close_db()
        assert "not yet implemented" in str(exc_info.value).lower()

    def test_database_config_placeholder(self):
        """Test that DatabaseConfig is a placeholder model."""
        config = DatabaseConfig()
        assert config.database_url is None

        config_with_url = DatabaseConfig(database_url="postgresql://test")
        assert config_with_url.database_url == "postgresql://test"
