"""Unit tests for VarReference dataclass."""

from typing import Any

import pytest

from hatch_global_env_vars.plugin import VarReference


class TestVarReference:
    """Test VarReference dataclass."""

    @pytest.mark.parametrize(
        (
            "name",
            "default",
            "expected_name",
            "expected_default",
        ),
        [
            (
                "MY_VAR",
                None,
                "MY_VAR",
                None,
            ),
            (
                "MY_VAR",
                "fallback",
                "MY_VAR",
                "fallback",
            ),
        ],
        ids=[
            "no_default",
            "with_string_default",
        ],
    )
    def test_reference_creation(
        self,
        name: str,
        default: str | None,
        expected_name: str,
        expected_default: str | None,
    ) -> None:
        """Test creating variable references with different defaults."""
        ref = VarReference(
            name=name,
            default=default,
        )
        assert ref.name == expected_name
        assert ref.default == expected_default

    def test_reference_with_nested_default(self) -> None:
        """Test variable reference with nested default."""
        nested = VarReference(
            name="NESTED",
            default="deep_fallback",
        )
        ref = VarReference(
            name="MY_VAR",
            default=nested,
        )
        assert ref.name == "MY_VAR"
        assert getattr(ref.default, "name") == "NESTED"
        assert getattr(ref.default, "default") == "deep_fallback"

    @pytest.mark.parametrize(
        (
            "input_dict",
            "expected_name",
            "expected_default",
        ),
        [
            (
                {
                    "name": "MY_VAR",
                },
                "MY_VAR",
                None,
            ),
            (
                {
                    "name": "MY_VAR",
                    "default": "fallback",
                },
                "MY_VAR",
                "fallback",
            ),
        ],
        ids=[
            "no_default",
            "with_default",
        ],
    )
    def test_from_dict(
        self,
        input_dict: dict[str, Any],
        expected_name: str,
        expected_default: str | None,
    ) -> None:
        """Test creating VarReference from dict with various configurations."""
        ref = VarReference.from_dict(
            input_dict,
        )
        assert ref.name == expected_name
        assert ref.default == expected_default

    def test_from_dict_with_nested_default(self) -> None:
        """Test creating VarReference from dict with nested default."""
        ref = VarReference.from_dict(
            {
                "name": "MY_VAR",
                "default": {
                    "name": "NESTED",
                    "default": "deep_fallback",
                },
            },
        )
        assert ref.name == "MY_VAR"
        assert isinstance(
            ref.default,
            VarReference,
        )
        assert ref.default.name == "NESTED"
        assert ref.default.default == "deep_fallback"

    def test_from_dict_missing_name(self) -> None:
        """Test that missing name field raises error."""
        with pytest.raises(
            ValueError,
            match="must have 'name' field",
        ):
            VarReference.from_dict(
                {
                    "default": "value",
                },
            )
