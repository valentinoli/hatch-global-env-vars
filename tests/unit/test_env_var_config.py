"""Unit tests for EnvVarConfig dataclass."""

from typing import Any

import pytest

from hatch_global_env_vars.plugin import EnvVarConfig, VarReference


class TestEnvVarConfig:
    """Test EnvVarConfig dataclass."""

    @pytest.mark.parametrize(
        (
            "kwargs",
            "expected_copy",
            "expected_value",
        ),
        [
            (
                {
                    "name": "TARGET",
                    "copy": "SOURCE",
                },
                "SOURCE",
                None,
            ),
            (
                {
                    "name": "TARGET",
                    "value": "literal",
                },
                None,
                "literal",
            ),
        ],
        ids=[
            "copy_mode",
            "value_mode",
        ],
    )
    def test_config_modes(
        self,
        kwargs: dict[str, Any],
        expected_copy: str | None,
        expected_value: str | None,
    ) -> None:
        """Test configuration in different modes."""
        config = EnvVarConfig(
            **kwargs,
        )
        assert config.name == "TARGET"
        assert config.copy == expected_copy
        assert config.value == expected_value

    def test_copy_with_default(self) -> None:
        """Test copy mode with default fallback."""
        config = EnvVarConfig(
            name="TARGET",
            copy="SOURCE",
            default="fallback",
            required=False,
        )
        assert config.default == "fallback"

    @pytest.mark.parametrize(
        (
            "kwargs",
            "error_match",
        ),
        [
            (
                {
                    "name": "TARGET",
                },
                "must have either 'copy' or 'value'",
            ),
            (
                {
                    "name": "TARGET",
                    "copy": "SOURCE",
                    "value": "literal",
                },
                "cannot have both 'copy' and 'value'",
            ),
            (
                {
                    "name": "TARGET",
                    "value": "literal",
                    "default": "fallback",
                },
                "cannot have 'default' when using 'value'",
            ),
        ],
        ids=[
            "missing_copy_and_value",
            "both_copy_and_value",
            "default_with_value",
        ],
    )
    def test_validation_errors(
        self,
        kwargs: dict[str, Any],
        error_match: str,
    ) -> None:
        """Test various validation errors."""
        with pytest.raises(
            ValueError,
            match=error_match,
        ):
            EnvVarConfig(
                **kwargs,
            )

    @pytest.mark.parametrize(
        (
            "input_dict",
            "expected_copy",
            "expected_value",
        ),
        [
            (
                {
                    "name": "TARGET",
                    "copy": "SOURCE",
                },
                "SOURCE",
                None,
            ),
            (
                {
                    "name": "TARGET",
                    "value": "literal",
                },
                None,
                "literal",
            ),
        ],
        ids=[
            "copy_mode",
            "value_mode",
        ],
    )
    def test_from_dict_modes(
        self,
        input_dict: dict[str, Any],
        expected_copy: str | None,
        expected_value: str | None,
    ) -> None:
        """Test creating config from dict in different modes."""
        config = EnvVarConfig.from_dict(
            input_dict,
        )
        assert config.name == "TARGET"
        assert config.copy == expected_copy
        assert config.value == expected_value

    def test_from_dict_with_var_reference(self) -> None:
        """Test creating config with VarReference value."""
        config = EnvVarConfig.from_dict(
            {
                "name": "TARGET",
                "value": {
                    "name": "SOURCE",
                    "default": "fallback",
                },
            },
        )
        assert config.name == "TARGET"
        assert isinstance(
            config.value,
            VarReference,
        )
        assert config.value.name == "SOURCE"

    def test_from_dict_with_dict_default(self) -> None:
        """Test creating config with VarReference as default."""
        config = EnvVarConfig.from_dict(
            {
                "name": "TARGET",
                "copy": "SOURCE",
                "default": {
                    "name": "FALLBACK",
                    "default": "final_value",
                },
            },
        )
        assert config.name == "TARGET"
        assert config.copy == "SOURCE"
        assert isinstance(
            config.default,
            VarReference,
        )
        assert config.default.name == "FALLBACK"
        assert config.default.default == "final_value"

    def test_from_dict_with_condition(self) -> None:
        """Test creating config with condition."""
        config = EnvVarConfig.from_dict(
            {
                "name": "TARGET",
                "value": "literal",
                "condition": "CI",
            },
        )
        assert config.condition == "CI"

    @pytest.mark.parametrize(
        (
            "input_data",
            "error_type",
            "error_match",
        ),
        [
            (
                {
                    "copy": "SOURCE",
                },
                ValueError,
                "must have 'name' field",
            ),
            (
                "not a dict",
                TypeError,
                "must be a dict",
            ),
        ],
        ids=[
            "missing_name",
            "not_a_dict",
        ],
    )
    def test_from_dict_errors(
        self,
        input_data: Any,
        error_type: type[Exception],
        error_match: str,
    ) -> None:
        """Test from_dict error handling."""
        with pytest.raises(
            error_type,
            match=error_match,
        ):
            EnvVarConfig.from_dict(
                input_data,
            )
