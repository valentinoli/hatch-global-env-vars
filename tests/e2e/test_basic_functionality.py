"""End-to-end tests for basic plugin functionality."""

from pathlib import Path

from tests.e2e.helpers import build_pyproject
from tests.utils import create_test_project, get_env_vars_in_hatch_env


class TestBasicFunctionality:
    """Test basic plugin functionality in real Hatch environments."""

    def test_copy_with_fallback(self, tmp_path: Path) -> None:
        """Test copying environment variable with fallback."""
        pyproject_content = build_pyproject(
            '    { name = "LOG_LEVEL", copy = "CI_LOG_LEVEL", default = "info", required = false },'
        )
        with create_test_project(tmp_path, pyproject_content):
            # Test with CI_LOG_LEVEL set
            env_vars = get_env_vars_in_hatch_env(
                ["LOG_LEVEL"],
                env={"CI_LOG_LEVEL": "debug"},
            )
            assert env_vars["LOG_LEVEL"] == "debug"

            # Test without CI_LOG_LEVEL (should use default)
            env_vars = get_env_vars_in_hatch_env(
                ["LOG_LEVEL"],
            )
            assert env_vars["LOG_LEVEL"] == "info"

    def test_literal_value(self, tmp_path: Path) -> None:
        """Test setting a literal value."""
        pyproject_content = build_pyproject(
            '    { name = "APP_NAME", value = "my-app" },'
        )
        with create_test_project(tmp_path, pyproject_content):
            env_vars = get_env_vars_in_hatch_env(
                ["APP_NAME"],
            )
            assert env_vars["APP_NAME"] == "my-app"

    def test_optional_copy(self, tmp_path: Path) -> None:
        """Test optional copy that doesn't fail when source is missing."""
        pyproject_content = build_pyproject(
            '    { name = "API_KEY", copy = "SECRET_API_KEY", required = false },'
        )
        with create_test_project(tmp_path, pyproject_content):
            # Should not fail, just not set the variable
            env_vars = get_env_vars_in_hatch_env(
                ["API_KEY"],
            )
            assert env_vars["API_KEY"] is None
