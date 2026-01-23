"""End-to-end tests for complex real-world scenarios."""

from pathlib import Path

import pytest

from tests.e2e.helpers import build_pyproject
from tests.utils import create_test_project, get_env_vars_in_hatch_env


class TestComplexScenarios:
    """Test complex real-world scenarios."""

    @pytest.mark.parametrize(
        (
            "env",
            "expected_is_ci",
            "expected_log_level",
            "expected_deploy",
        ),
        [
            (
                {},
                "false",
                "info",
                None,
            ),
            (
                {"CUSTOM_CI": "true", "BRANCH": "feature"},
                "true",
                "debug",
                None,
            ),
            (
                {"CUSTOM_CI": "true", "BRANCH": "main"},
                "true",
                "debug",
                "true",
            ),
        ],
        ids=[
            "local_development",
            "ci_feature_branch",
            "ci_main_branch",
        ],
    )
    def test_ci_detection_scenario(
        self,
        tmp_path: Path,
        env: dict[str, str],
        expected_is_ci: str,
        expected_log_level: str,
        expected_deploy: str | None,
    ) -> None:
        """Test a realistic CI detection setup."""
        pyproject_content = build_pyproject(
            """    { name = "IS_CI", copy = "CUSTOM_CI", default = "false" },
    { name = "LOG_LEVEL", value = "debug", condition = "CUSTOM_CI" },
    { name = "LOG_LEVEL", value = "info", condition = "!CUSTOM_CI" },
    { name = "DEPLOY", value = "true", condition = ["CUSTOM_CI", "BRANCH==main"] },"""
        )
        with create_test_project(tmp_path, pyproject_content):
            env_vars = get_env_vars_in_hatch_env(
                ["IS_CI", "LOG_LEVEL", "DEPLOY"],
                env=env,
            )
            assert env_vars["IS_CI"] == expected_is_ci
            assert env_vars["LOG_LEVEL"] == expected_log_level
            assert env_vars["DEPLOY"] == expected_deploy

    @pytest.mark.parametrize(
        (
            "env",
            "expected_app_env",
            "expected_database_url",
        ),
        [
            (
                {"ENVIRONMENT": "production", "PROD_DB": "postgres://prod"},
                "production",
                "postgres://prod",
            ),
            (
                {"ENVIRONMENT": "staging", "STAGE_DB": "postgres://stage"},
                "staging",
                "postgres://stage",
            ),
            (
                {},
                "development",
                "sqlite:///dev.db",
            ),
        ],
        ids=[
            "production",
            "staging",
            "development",
        ],
    )
    def test_multi_environment_setup(
        self,
        tmp_path: Path,
        env: dict[str, str],
        expected_app_env: str,
        expected_database_url: str,
    ) -> None:
        """Test environment-specific configuration."""
        pyproject_content = build_pyproject(
            """    { name = "APP_ENV", copy = "ENVIRONMENT", default = "development" },
    { name = "DATABASE_URL", copy = "PROD_DB", condition = "ENVIRONMENT==production" },
    { name = "DATABASE_URL", copy = "STAGE_DB", condition = "ENVIRONMENT==staging" },
    { name = "DATABASE_URL", value = "sqlite:///dev.db", condition = { any = ["!ENVIRONMENT", "ENVIRONMENT==development"] } },"""
        )
        with create_test_project(tmp_path, pyproject_content):
            env_vars = get_env_vars_in_hatch_env(
                ["APP_ENV", "DATABASE_URL"],
                env=env,
            )
            assert env_vars["APP_ENV"] == expected_app_env
            assert env_vars["DATABASE_URL"] == expected_database_url
