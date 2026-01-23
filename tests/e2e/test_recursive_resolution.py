"""End-to-end tests for recursive variable reference resolution."""

from pathlib import Path

import pytest

from tests.e2e.helpers import build_pyproject
from tests.utils import create_test_project, get_env_vars_in_hatch_env


class TestRecursiveResolution:
    """Test recursive variable reference resolution."""

    @pytest.mark.parametrize(
        (
            "env",
            "expected",
        ),
        [
            (
                {"DEPLOY_ENV": "production"},
                "production",
            ),
            (
                {"ENVIRONMENT": "staging"},
                "staging",
            ),
            (
                {},
                "development",
            ),
        ],
        ids=[
            "first_level_set",
            "second_level_set",
            "use_final_default",
        ],
    )
    def test_simple_recursive_fallback(
        self,
        tmp_path: Path,
        env: dict[str, str],
        expected: str,
    ) -> None:
        """Test two-level fallback chain."""
        pyproject_content = build_pyproject(
            '    { name = "APP_ENV", copy = "DEPLOY_ENV", default = { name = "ENVIRONMENT", default = "development" } },'
        )
        with create_test_project(tmp_path, pyproject_content):
            env_vars = get_env_vars_in_hatch_env(
                ["APP_ENV"],
                env=env,
            )
            assert env_vars["APP_ENV"] == expected

    @pytest.mark.parametrize(
        (
            "env",
            "expected",
        ),
        [
            (
                {"PROD_CONFIG": "prod.yaml"},
                "prod.yaml",
            ),
            (
                {"STAGE_CONFIG": "stage.yaml"},
                "stage.yaml",
            ),
            (
                {"DEV_CONFIG": "dev.yaml"},
                "dev.yaml",
            ),
            (
                {},
                "config.yaml",
            ),
        ],
        ids=[
            "first_level",
            "second_level",
            "third_level",
            "final_default",
        ],
    )
    def test_deep_recursive_fallback(
        self,
        tmp_path: Path,
        env: dict[str, str],
        expected: str,
    ) -> None:
        """Test multi-level fallback chain."""
        pyproject_content = build_pyproject(
            '    { name = "CONFIG", copy = "PROD_CONFIG", default = { name = "STAGE_CONFIG", default = { name = "DEV_CONFIG", default = "config.yaml" } } },'
        )
        with create_test_project(tmp_path, pyproject_content):
            env_vars = get_env_vars_in_hatch_env(
                ["CONFIG"],
                env=env,
            )
            assert env_vars["CONFIG"] == expected
