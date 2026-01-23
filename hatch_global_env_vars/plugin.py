"""
Hatch environment collector plugin for dynamic global environment variable setting.

This plugin sets environment variables globally using os.environ during Hatch's
environment initialization, before any environments are created.

Installation:
    Add to your pyproject.toml:

    [tool.hatch.env]
    requires = ["hatch-global-env-vars"]

Usage in pyproject.toml:
    [tool.hatch.env.collectors.global-env-vars]
    env-vars = [
        # Copy from another env var with fallback
        { name = "LOG_LEVEL", copy = "CI_LOG_LEVEL", default = "info" },

        # Copy only if source exists (optional)
        { name = "API_KEY", copy = "SECRET_API_KEY", required = false },

        # Simple conditions
        { name = "HAS_CONFIG", value = "true", condition = "CONFIG_FILE" },  # exists
        { name = "NO_CONFIG", value = "true", condition = "!CONFIG_FILE" },  # doesn't exist

        # Empty/non-empty checks
        { name = "IS_EMPTY", value = "true", condition = "TOKEN==" },   # exists and empty
        { name = "HAS_VALUE", value = "true", condition = "TOKEN!=" },  # exists and non-empty

        # Value comparisons
        { name = "VERBOSE", value = "true", condition = "LOG_LEVEL==debug" },

        # Multiple conditions (AND logic)
        { name = "DEPLOY", value = "true", condition = ["CI", "BRANCH==main"] },

        # OR logic
        { name = "CACHE", value = "redis", condition = { any = ["PROD", "STAGING"] } },

        # Recursive resolution
        { name = "APP_ENV", copy = "ENVIRONMENT", default = { name = "ENV", default = "development" } },
    ]
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, TypeAlias

from hatch.env.collectors.plugin.interface import EnvironmentCollectorInterface

# Type definitions for conditions
Condition: TypeAlias = str | list[str] | dict[str, list[str]]


@dataclass
class VarReference:
    """Reference to another environment variable with optional default."""

    name: str
    default: str | "VarReference" | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VarReference":
        """Create a VarReference from a dictionary."""
        if "name" not in data:
            raise ValueError(f"Variable reference must have 'name' field: {data}")

        name = data["name"]
        default = data.get("default")

        # Recursively parse nested defaults
        if isinstance(default, dict):
            default = cls.from_dict(default)

        return cls(
            name=name,
            default=default,
        )


@dataclass
class EnvVarConfig:
    """Configuration for a single environment variable."""

    name: str
    copy: str | None = None
    value: str | VarReference | None = None
    default: str | VarReference | None = None
    required: bool = True
    condition: Condition | None = None

    def __post_init__(self):
        """Validate the configuration after initialization."""
        self._validate()

    def _validate(self) -> None:
        """Validate the configuration."""
        # Must have either copy or value
        if self.copy is None and self.value is None:
            raise ValueError(
                f"Environment variable '{self.name}' must have either 'copy' or 'value'",
            )

        # Cannot have both copy and value
        if self.copy is not None and self.value is not None:
            raise ValueError(
                f"Environment variable '{self.name}' cannot have both 'copy' and 'value'",
            )

        # If using 'value', default should not be present
        if self.value is not None and self.default is not None:
            raise ValueError(
                f"Environment variable '{self.name}' cannot have 'default' when using 'value'",
            )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EnvVarConfig":
        """Create an EnvVarConfig from a dictionary."""
        if not isinstance(data, dict):
            raise TypeError(
                f"Environment variable configuration must be a dict, got {type(data)}",
            )

        if "name" not in data:
            raise ValueError(
                "Environment variable configuration must have 'name' field",
            )

        name = data["name"]
        copy = data.get("copy")
        value = data.get("value")
        default = data.get("default")
        required = data.get("required", True)
        condition = data.get("condition")

        # Parse value if it's a dict (variable reference)
        if isinstance(value, dict):
            value = VarReference.from_dict(value)

        # Parse default if it's a dict (variable reference)
        if isinstance(default, dict):
            default = VarReference.from_dict(default)

        return cls(
            name=name,
            copy=copy,
            value=value,
            default=default,
            required=required,
            condition=condition,
        )


class GlobalEnvVarsCollector(EnvironmentCollectorInterface):
    """Environment collector that sets global environment variables."""

    PLUGIN_NAME = "global-env-vars"

    def __init__(  # no cov
        self,
        *args,
        **kwargs,
    ):
        super().__init__(  # no cov
            *args,
            **kwargs,
        )
        # Process and set environment variables immediately upon initialization
        self._set_global_env_vars()  # no cov

    def _set_global_env_vars(
        self,
    ) -> None:
        """Process configuration and set global environment variables."""
        env_var_configs_raw = self.config.get("env-vars", [])

        if not isinstance(env_var_configs_raw, list):
            raise TypeError("env-vars must be a list")

        # Parse and validate all configurations
        env_var_configs: list[EnvVarConfig] = []
        for i, raw_config in enumerate(env_var_configs_raw):
            try:
                config = EnvVarConfig.from_dict(raw_config)
                env_var_configs.append(config)
            except (ValueError, TypeError) as e:
                raise type(e)(f"Error in env-vars[{i}]: {e}") from e

        # Set the environment variables
        for config in env_var_configs:
            self._process_env_var(config)

    @staticmethod
    def _process_env_var(
        config: EnvVarConfig,
    ) -> None:
        """Process a single environment variable configuration and set it globally."""
        # Check condition if present
        if config.condition is not None:
            if not GlobalEnvVarsCollector._evaluate_condition(config.condition):
                return

        # Determine the value to set
        value = None

        if config.copy is not None:
            # Copy mode
            if config.copy in os.environ:
                source_value = os.environ[config.copy]
                value = GlobalEnvVarsCollector._resolve_value(
                    source_value,
                )
            elif config.default is not None:
                value = GlobalEnvVarsCollector._resolve_value(
                    config.default,
                )
            elif config.required:
                raise ValueError(
                    f"Required environment variable '{config.copy}' not found "
                    f"for '{config.name}'"
                )
        elif config.value is not None:
            # Value mode
            value = GlobalEnvVarsCollector._resolve_value(
                config.value,
            )

        # Set the environment variable globally if we have a value
        if value is not None:
            os.environ[config.name] = value

    @staticmethod
    def _resolve_value(
        value: str | VarReference,
        visited: set[str] | None = None,
    ) -> str | None:
        """
        Recursively resolve environment variable references.

        Args:
            value: Either a string literal or a VarReference
            visited: Set of variable names being resolved (for cycle detection)

        Returns:
            Resolved string or None if a required variable is missing
        """
        if visited is None:
            visited = set()

        # If value is a VarReference, resolve it
        if isinstance(value, VarReference):
            var_name = value.name

            # Check for circular references
            if var_name in visited:
                raise ValueError(f"Circular reference detected: {var_name}")

            env_value = os.environ.get(var_name)

            if env_value is not None:
                return env_value
            elif value.default is not None:
                # Recursively resolve the default value
                visited.add(var_name)
                resolved = GlobalEnvVarsCollector._resolve_value(
                    value.default,
                    visited,
                )
                visited.discard(var_name)
                return resolved
            else:
                # No value and no default
                return None

        # If value is a string, return it as-is
        return value

    @staticmethod
    def _evaluate_condition(
        condition: Condition,
    ) -> bool:
        """
        Evaluate a condition expression.

        Supports:
        - String conditions:
          - "ENV": true if ENV exists (regardless of value)
          - "!ENV": true if ENV doesn't exist
          - "ENV==": true if ENV exists and is empty string
          - "ENV!=": true if ENV exists and is non-empty
          - "ENV==value": true if ENV equals value (value must be non-empty)
          - "ENV!=value": true if ENV doesn't equal value
        - List conditions: AND logic (all must be true)
        - Dict conditions: {"any": [...]} for OR, {"all": [...]} for AND

        Args:
            condition: Condition to evaluate

        Returns:
            True if condition is met, False otherwise
        """
        # Handle list (AND logic)
        if isinstance(condition, list):
            return all(
                GlobalEnvVarsCollector._evaluate_condition(cond) for cond in condition
            )

        # Handle dict (OR/AND logic)
        if isinstance(condition, dict):
            if "any" in condition:
                conditions = condition["any"]
                if not isinstance(conditions, list):
                    raise ValueError("'any' condition must contain a list")
                return any(
                    GlobalEnvVarsCollector._evaluate_condition(cond)
                    for cond in conditions
                )
            elif "all" in condition:
                conditions = condition["all"]
                if not isinstance(conditions, list):
                    raise ValueError("'all' condition must contain a list")
                return all(
                    GlobalEnvVarsCollector._evaluate_condition(cond)
                    for cond in conditions
                )
            else:
                raise ValueError(f"Unknown condition dict format: {condition}")

        # Handle string conditions
        if not isinstance(condition, str):
            raise TypeError(
                f"Condition must be string, list, or dict, got {type(condition)}",
            )

        condition = condition.strip()

        # Check for equality operator
        if "==" in condition:
            parts = condition.split(
                "==",
                1,
            )
            if len(parts) != 2:  # no cov
                raise ValueError(f"Invalid equality condition: {condition}")
            var_name = parts[0].strip()
            expected_value = parts[1].strip()

            # Check if variable exists
            if var_name not in os.environ:
                return False

            actual_value = os.environ[var_name]
            return actual_value == expected_value

        # Check for inequality operator
        if "!=" in condition:
            parts = condition.split(
                "!=",
                1,
            )
            if len(parts) != 2:  # no cov
                raise ValueError(f"Invalid inequality condition: {condition}")
            var_name = parts[0].strip()
            expected_value = parts[1].strip()

            # Check if variable exists
            if var_name not in os.environ:
                return False

            actual_value = os.environ[var_name]
            return actual_value != expected_value

        # Check for simple negation (does not exist)
        if condition.startswith("!"):
            var_name = condition[1:].strip()
            return var_name not in os.environ

        # Default: exists check
        return condition in os.environ
