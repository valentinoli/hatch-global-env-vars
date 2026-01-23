"""Helper function for e2e tests."""


def build_pyproject(env_vars_config: str) -> str:
    """Build pyproject.toml content with the given env-vars configuration."""
    return f"""
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "test-package"
version = "0.1.0"

[tool.hatch.env]
requires = ["hatch-global-env-vars"]

[tool.hatch.env.collectors.global-env-vars]
env-vars = [
{env_vars_config}
]
"""
