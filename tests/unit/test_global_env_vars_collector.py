"""Unit tests for GlobalEnvVarsCollector error handling."""

import os
from unittest.mock import patch

import pytest

from hatch_global_env_vars.plugin import (
    EnvVarConfig,
    GlobalEnvVarsCollector,
    VarReference,
)


class TestGlobalEnvVarsCollector:
    """Test GlobalEnvVarsCollector error handling."""

    def setup_method(self) -> None:
        """Set up test environment."""
        self.original_env = os.environ.copy()
        os.environ.clear()

    def teardown_method(self) -> None:
        """Restore original environment."""
        os.environ.clear()
        os.environ.update(
            self.original_env,
        )

    def test_env_vars_not_a_list(self) -> None:
        """Test that env-vars must be a list."""
        collector = GlobalEnvVarsCollector.__new__(
            GlobalEnvVarsCollector,
        )

        # Mock the config property
        mock_config = {
            "env-vars": "not a list",
        }

        with pytest.raises(
            TypeError,
            match="env-vars must be a list",
        ):
            with patch.object(
                type(collector),
                "config",
                new_callable=lambda: property(lambda self: mock_config),
            ):
                collector._set_global_env_vars()

    def test_invalid_config_in_list(self) -> None:
        """Test error handling when parsing invalid config."""
        collector = GlobalEnvVarsCollector.__new__(
            GlobalEnvVarsCollector,
        )

        # Mock the config property with invalid config
        mock_config = {
            "env-vars": [
                {
                    "invalid": "config",
                },
            ],
        }

        with pytest.raises(
            ValueError,
            match=r"Error in env-vars\[0\]",
        ):
            with patch.object(
                type(collector),
                "config",
                new_callable=lambda: property(lambda self: mock_config),
            ):
                collector._set_global_env_vars()

    def test_required_copy_not_found(self) -> None:
        """Test ValueError when required copy source is not found."""
        collector = GlobalEnvVarsCollector.__new__(
            GlobalEnvVarsCollector,
        )

        # Mock the config property
        mock_config = {
            "env-vars": [
                {
                    "name": "TARGET",
                    "copy": "SOURCE",
                    "required": True,
                },
            ],
        }

        with pytest.raises(
            ValueError,
            match="Required environment variable 'SOURCE' not found",
        ):
            with patch.object(
                type(collector),
                "config",
                new_callable=lambda: property(lambda self: mock_config),
            ):
                collector._set_global_env_vars()

    def test_process_env_var_with_false_condition(self) -> None:
        """Test that env var is not set when condition is false."""
        config = EnvVarConfig(
            name="TARGET",
            value="test",
            condition="MISSING_VAR",
        )

        # Ensure MISSING_VAR doesn't exist
        os.environ.pop(
            "MISSING_VAR",
            None,
        )
        os.environ.pop(
            "TARGET",
            None,
        )

        GlobalEnvVarsCollector._process_env_var(
            config,
        )

        # TARGET should not be set
        assert "TARGET" not in os.environ

    def test_process_env_var_copy_from_existing(self) -> None:
        """Test copying from an existing environment variable."""
        os.environ["SOURCE"] = "source_value"
        os.environ.pop(
            "TARGET",
            None,
        )

        config = EnvVarConfig(
            name="TARGET",
            copy="SOURCE",
        )

        GlobalEnvVarsCollector._process_env_var(
            config,
        )

        assert os.environ["TARGET"] == "source_value"

    def test_process_env_var_copy_with_default(self) -> None:
        """Test copying with default when source doesn't exist."""
        os.environ.pop(
            "SOURCE",
            None,
        )
        os.environ.pop(
            "TARGET",
            None,
        )

        config = EnvVarConfig(
            name="TARGET",
            copy="SOURCE",
            default="default_value",
            required=False,
        )

        GlobalEnvVarsCollector._process_env_var(
            config,
        )

        assert os.environ["TARGET"] == "default_value"

    def test_process_env_var_with_value(self) -> None:
        """Test setting a literal value."""
        os.environ.pop(
            "TARGET",
            None,
        )

        config = EnvVarConfig(
            name="TARGET",
            value="literal_value",
        )

        GlobalEnvVarsCollector._process_env_var(
            config,
        )

        assert os.environ["TARGET"] == "literal_value"

    def test_process_env_var_with_var_reference_value(self) -> None:
        """Test setting value using VarReference."""
        os.environ["REF_VAR"] = "ref_value"
        os.environ.pop(
            "TARGET",
            None,
        )

        config = EnvVarConfig(
            name="TARGET",
            value=VarReference(
                name="REF_VAR",
            ),
        )

        GlobalEnvVarsCollector._process_env_var(
            config,
        )

        assert os.environ["TARGET"] == "ref_value"
