"""Unit tests for value resolution with VarReference."""

import os

import pytest

from hatch_global_env_vars.plugin import GlobalEnvVarsCollector, VarReference


class TestValueResolution:
    """Test value resolution with VarReference."""

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

    def test_resolve_string(self) -> None:
        """Test resolving a simple string."""
        result = GlobalEnvVarsCollector._resolve_value(
            "literal",
        )
        assert result == "literal"

    @pytest.mark.parametrize(
        (
            "env_vars",
            "var_ref",
            "expected",
        ),
        [
            (
                {
                    "SOURCE": "value",
                },
                VarReference(
                    name="SOURCE",
                ),
                "value",
            ),
            (
                {},
                VarReference(
                    name="SOURCE",
                    default="fallback",
                ),
                "fallback",
            ),
            (
                {},
                VarReference(
                    name="SOURCE",
                ),
                None,
            ),
        ],
        ids=[
            "var_exists",
            "use_default",
            "no_value_no_default",
        ],
    )
    def test_resolve_var_reference(
        self,
        env_vars: dict[str, str],
        var_ref: VarReference,
        expected: str | None,
    ) -> None:
        """Test resolving VarReference in various scenarios."""
        os.environ.update(
            env_vars,
        )
        result = GlobalEnvVarsCollector._resolve_value(
            var_ref,
        )
        assert result == expected

    def test_resolve_var_reference_nested_default(self) -> None:
        """Test resolving VarReference with nested defaults."""
        os.environ["THIRD"] = "final_value"
        ref = VarReference(
            name="FIRST",
            default=VarReference(
                name="SECOND",
                default=VarReference(
                    name="THIRD",
                ),
            ),
        )
        result = GlobalEnvVarsCollector._resolve_value(
            ref,
        )
        assert result == "final_value"

    def test_circular_reference_detection(self) -> None:
        """Test that circular references are detected."""
        os.environ["VAR1"] = "value"

        with pytest.raises(
            ValueError,
            match="Circular reference detected",
        ):
            GlobalEnvVarsCollector._resolve_value(
                VarReference(
                    name="VAR1",
                ),
                visited={
                    "VAR1",
                },
            )
