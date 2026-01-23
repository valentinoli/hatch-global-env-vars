"""End-to-end tests for conditional environment variable setting."""

from pathlib import Path

import pytest

from tests.e2e.helpers import build_pyproject
from tests.utils import create_test_project, get_env_vars_in_hatch_env


class TestConditions:
    """Test conditional environment variable setting."""

    @pytest.mark.parametrize(
        (
            "env",
            "expected",
        ),
        [
            (
                {"CUSTOM_CI": "true"},
                "true",
            ),
            (
                {},
                None,
            ),
        ],
        ids=[
            "with_ci",
            "without_ci",
        ],
    )
    def test_exists_condition(
        self,
        tmp_path: Path,
        env: dict[str, str],
        expected: str | None,
    ) -> None:
        """Test condition based on variable existence."""
        pyproject_content = build_pyproject(
            '    { name = "IS_CI", value = "true", condition = "CUSTOM_CI" },'
        )
        with create_test_project(tmp_path, pyproject_content):
            env_vars = get_env_vars_in_hatch_env(
                ["IS_CI"],
                env=env,
            )
            assert env_vars["IS_CI"] == expected

    @pytest.mark.parametrize(
        (
            "env",
            "expected",
        ),
        [
            (
                {},
                "true",
            ),
            (
                {"CUSTOM_CI": "true"},
                None,
            ),
        ],
        ids=[
            "without_ci",
            "with_ci",
        ],
    )
    def test_not_exists_condition(
        self,
        tmp_path: Path,
        env: dict[str, str],
        expected: str | None,
    ) -> None:
        """Test negated existence condition."""
        pyproject_content = build_pyproject(
            '    { name = "LOCAL_DEV", value = "true", condition = "!CUSTOM_CI" },'
        )
        with create_test_project(tmp_path, pyproject_content):
            env_vars = get_env_vars_in_hatch_env(
                ["LOCAL_DEV"],
                env=env,
            )
            assert env_vars["LOCAL_DEV"] == expected

    @pytest.mark.parametrize(
        (
            "env",
            "expected",
        ),
        [
            (
                {"LOG_LEVEL": "debug"},
                "true",
            ),
            (
                {"LOG_LEVEL": "info"},
                None,
            ),
        ],
        ids=[
            "log_level_debug",
            "log_level_info",
        ],
    )
    def test_equality_condition(
        self,
        tmp_path: Path,
        env: dict[str, str],
        expected: str | None,
    ) -> None:
        """Test equality condition."""
        pyproject_content = build_pyproject(
            '    { name = "VERBOSE", value = "true", condition = "LOG_LEVEL==debug" },'
        )
        with create_test_project(tmp_path, pyproject_content):
            env_vars = get_env_vars_in_hatch_env(
                ["VERBOSE"],
                env=env,
            )
            assert env_vars["VERBOSE"] == expected

    @pytest.mark.parametrize(
        (
            "env",
            "expected",
        ),
        [
            (
                {"CONFIG": ""},
                "true",
            ),
            (
                {"CONFIG": "custom.yaml"},
                None,
            ),
        ],
        ids=[
            "config_empty",
            "config_has_value",
        ],
    )
    def test_empty_check_condition(
        self,
        tmp_path: Path,
        env: dict[str, str],
        expected: str | None,
    ) -> None:
        """Test empty string check condition."""
        pyproject_content = build_pyproject(
            '    { name = "USE_DEFAULT", value = "true", condition = "CONFIG==" },'
        )
        with create_test_project(tmp_path, pyproject_content):
            env_vars = get_env_vars_in_hatch_env(
                ["USE_DEFAULT"],
                env=env,
            )
            assert env_vars["USE_DEFAULT"] == expected

    @pytest.mark.parametrize(
        (
            "env",
            "expected",
        ),
        [
            (
                {"AUTH_TOKEN": "secret123"},
                "true",
            ),
            (
                {"AUTH_TOKEN": ""},
                None,
            ),
        ],
        ids=[
            "token_has_value",
            "token_empty",
        ],
    )
    def test_non_empty_check_condition(
        self,
        tmp_path: Path,
        env: dict[str, str],
        expected: str | None,
    ) -> None:
        """Test non-empty string check condition."""
        pyproject_content = build_pyproject(
            '    { name = "HAS_TOKEN", value = "true", condition = "AUTH_TOKEN!=" },'
        )
        with create_test_project(tmp_path, pyproject_content):
            env_vars = get_env_vars_in_hatch_env(
                ["HAS_TOKEN"],
                env=env,
            )
            assert env_vars["HAS_TOKEN"] == expected

    @pytest.mark.parametrize(
        (
            "env",
            "expected",
        ),
        [
            (
                {"CUSTOM_CI": "true", "BRANCH": "main"},
                "true",
            ),
            (
                {"CUSTOM_CI": "true", "BRANCH": "dev"},
                None,
            ),
        ],
        ids=[
            "both_conditions_met",
            "one_condition_met",
        ],
    )
    def test_and_condition(
        self,
        tmp_path: Path,
        env: dict[str, str],
        expected: str | None,
    ) -> None:
        """Test AND logic with list conditions."""
        pyproject_content = build_pyproject(
            '    { name = "DEPLOY", value = "true", condition = ["CUSTOM_CI", "BRANCH==main"] },'
        )
        with create_test_project(tmp_path, pyproject_content):
            env_vars = get_env_vars_in_hatch_env(
                ["DEPLOY"],
                env=env,
            )
            assert env_vars["DEPLOY"] == expected

    @pytest.mark.parametrize(
        (
            "env",
            "expected",
        ),
        [
            (
                {"PROD": "true"},
                "redis",
            ),
            (
                {"STAGING": "true"},
                "redis",
            ),
            (
                {},
                None,
            ),
        ],
        ids=[
            "first_condition_met",
            "second_condition_met",
            "no_conditions_met",
        ],
    )
    def test_or_condition(
        self,
        tmp_path: Path,
        env: dict[str, str],
        expected: str | None,
    ) -> None:
        """Test OR logic with dict conditions."""
        pyproject_content = build_pyproject(
            '    { name = "USE_CACHE", value = "redis", condition = { any = ["PROD", "STAGING"] } },'
        )
        with create_test_project(tmp_path, pyproject_content):
            env_vars = get_env_vars_in_hatch_env(
                ["USE_CACHE"],
                env=env,
            )
            assert env_vars["USE_CACHE"] == expected
