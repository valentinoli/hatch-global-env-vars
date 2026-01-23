"""Unit tests for condition evaluation error handling."""

import os

import pytest

from hatch_global_env_vars.plugin import GlobalEnvVarsCollector


class TestConditionEvaluationErrors:
    """Test error handling in condition evaluation."""

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

    def test_any_condition_not_a_list(self) -> None:
        """Test that 'any' condition must contain a list."""
        with pytest.raises(
            ValueError,
            match="'any' condition must contain a list",
        ):
            GlobalEnvVarsCollector._evaluate_condition(
                {
                    "any": "not a list",  # type: ignore[dict-item]
                }
            )

    def test_all_condition_not_a_list(self) -> None:
        """Test that 'all' condition must contain a list."""
        with pytest.raises(
            ValueError,
            match="'all' condition must contain a list",
        ):
            GlobalEnvVarsCollector._evaluate_condition(
                {
                    "all": "not a list",  # type: ignore[dict-item]
                }
            )

    def test_unknown_dict_format(self) -> None:
        """Test that unknown dict format raises error."""
        with pytest.raises(
            ValueError,
            match="Unknown condition dict format",
        ):
            GlobalEnvVarsCollector._evaluate_condition(
                {
                    "unknown": ["test"],
                },
            )

    def test_invalid_condition_type(self) -> None:
        """Test that invalid condition type raises error."""
        with pytest.raises(
            TypeError,
            match="Condition must be string, list, or dict",
        ):
            GlobalEnvVarsCollector._evaluate_condition(
                123,  # type: ignore[arg-type]
            )
