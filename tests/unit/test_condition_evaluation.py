"""Unit tests for condition evaluation logic."""

import os

import pytest

from hatch_global_env_vars.plugin import GlobalEnvVarsCollector


class TestConditionEvaluation:
    """Test condition evaluation logic."""

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

    @pytest.mark.parametrize(
        (
            "env_vars",
            "condition",
            "expected",
        ),
        [
            (
                {
                    "MY_VAR": "value",
                },
                "MY_VAR",
                True,
            ),
            (
                {},
                "MY_VAR",
                False,
            ),
            (
                {
                    "MY_VAR": "",
                },
                "MY_VAR",
                True,
            ),
        ],
        ids=[
            "var_exists_with_value",
            "var_not_set",
            "var_exists_empty",
        ],
    )
    def test_exists_check(
        self,
        env_vars: dict[str, str],
        condition: str,
        expected: bool,
    ) -> None:
        """Test ENV existence checks."""
        os.environ.update(
            env_vars,
        )
        assert (
            GlobalEnvVarsCollector._evaluate_condition(
                condition,
            )
            is expected
        )

    @pytest.mark.parametrize(
        (
            "env_vars",
            "condition",
            "expected",
        ),
        [
            (
                {},
                "!MY_VAR",
                True,
            ),
            (
                {
                    "MY_VAR": "value",
                },
                "!MY_VAR",
                False,
            ),
        ],
        ids=[
            "var_not_set",
            "var_exists",
        ],
    )
    def test_not_exists_check(
        self,
        env_vars: dict[str, str],
        condition: str,
        expected: bool,
    ) -> None:
        """Test !ENV non-existence checks."""
        os.environ.update(
            env_vars,
        )
        assert (
            GlobalEnvVarsCollector._evaluate_condition(
                condition,
            )
            is expected
        )

    @pytest.mark.parametrize(
        (
            "env_vars",
            "condition",
            "expected",
        ),
        [
            (
                {
                    "MY_VAR": "",
                },
                "MY_VAR==",
                True,
            ),
            (
                {},
                "MY_VAR==",
                False,
            ),
            (
                {
                    "MY_VAR": "value",
                },
                "MY_VAR==",
                False,
            ),
        ],
        ids=[
            "var_is_empty",
            "var_not_set",
            "var_has_value",
        ],
    )
    def test_empty_check(
        self,
        env_vars: dict[str, str],
        condition: str,
        expected: bool,
    ) -> None:
        """Test ENV== empty string checks."""
        os.environ.update(
            env_vars,
        )
        assert (
            GlobalEnvVarsCollector._evaluate_condition(
                condition,
            )
            is expected
        )

    @pytest.mark.parametrize(
        (
            "env_vars",
            "condition",
            "expected",
        ),
        [
            (
                {
                    "MY_VAR": "value",
                },
                "MY_VAR!=",
                True,
            ),
            (
                {
                    "MY_VAR": "",
                },
                "MY_VAR!=",
                False,
            ),
            (
                {},
                "MY_VAR!=",
                False,
            ),
        ],
        ids=[
            "var_has_value",
            "var_is_empty",
            "var_not_set",
        ],
    )
    def test_non_empty_check(
        self,
        env_vars: dict[str, str],
        condition: str,
        expected: bool,
    ) -> None:
        """Test ENV!= non-empty string checks."""
        os.environ.update(
            env_vars,
        )
        assert (
            GlobalEnvVarsCollector._evaluate_condition(
                condition,
            )
            is expected
        )

    @pytest.mark.parametrize(
        (
            "env_vars",
            "condition",
            "expected",
        ),
        [
            (
                {
                    "MY_VAR": "production",
                },
                "MY_VAR==production",
                True,
            ),
            (
                {
                    "MY_VAR": "development",
                },
                "MY_VAR==production",
                False,
            ),
        ],
        ids=[
            "values_match",
            "values_differ",
        ],
    )
    def test_equality_check(
        self,
        env_vars: dict[str, str],
        condition: str,
        expected: bool,
    ) -> None:
        """Test ENV==value equality checks."""
        os.environ.update(
            env_vars,
        )
        assert (
            GlobalEnvVarsCollector._evaluate_condition(
                condition,
            )
            is expected
        )

    @pytest.mark.parametrize(
        (
            "env_vars",
            "condition",
            "expected",
        ),
        [
            (
                {
                    "MY_VAR": "development",
                },
                "MY_VAR!=production",
                True,
            ),
            (
                {
                    "MY_VAR": "production",
                },
                "MY_VAR!=production",
                False,
            ),
        ],
        ids=[
            "values_differ",
            "values_match",
        ],
    )
    def test_inequality_check(
        self,
        env_vars: dict[str, str],
        condition: str,
        expected: bool,
    ) -> None:
        """Test ENV!=value inequality checks."""
        os.environ.update(
            env_vars,
        )
        assert (
            GlobalEnvVarsCollector._evaluate_condition(
                condition,
            )
            is expected
        )

    @pytest.mark.parametrize(
        (
            "env_vars",
            "condition",
            "expected",
        ),
        [
            (
                {
                    "VAR1": "yes",
                    "VAR2": "yes",
                },
                [
                    "VAR1",
                    "VAR2",
                ],
                True,
            ),
            (
                {
                    "VAR1": "yes",
                },
                [
                    "VAR1",
                    "VAR2",
                ],
                False,
            ),
        ],
        ids=[
            "all_vars_exist",
            "one_var_missing",
        ],
    )
    def test_and_logic(
        self,
        env_vars: dict[str, str],
        condition: list[str],
        expected: bool,
    ) -> None:
        """Test list conditions use AND logic."""
        os.environ.update(
            env_vars,
        )
        assert (
            GlobalEnvVarsCollector._evaluate_condition(
                condition,
            )
            is expected
        )

    @pytest.mark.parametrize(
        (
            "env_vars",
            "condition",
            "expected",
        ),
        [
            (
                {
                    "VAR1": "yes",
                },
                {
                    "any": [
                        "VAR1",
                        "VAR2",
                    ],
                },
                True,
            ),
            (
                {},
                {
                    "any": [
                        "VAR1",
                        "VAR2",
                    ],
                },
                False,
            ),
        ],
        ids=[
            "one_var_exists",
            "no_vars_exist",
        ],
    )
    def test_or_logic(
        self,
        env_vars: dict[str, str],
        condition: dict[str, list[str]],
        expected: bool,
    ) -> None:
        """Test 'any' dict uses OR logic."""
        os.environ.update(
            env_vars,
        )
        assert (
            GlobalEnvVarsCollector._evaluate_condition(
                condition,
            )
            is expected
        )

    def test_explicit_all_logic(self) -> None:
        """Test that 'all' dict works like list."""
        os.environ.update(
            {
                "VAR1": "yes",
                "VAR2": "yes",
            },
        )
        condition = {
            "all": [
                "VAR1",
                "VAR2",
            ],
        }
        assert (
            GlobalEnvVarsCollector._evaluate_condition(
                condition,
            )
            is True
        )
