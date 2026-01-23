import os
import subprocess
import sys
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any


def create_file(path: Path) -> None:
    """Create an empty file at the given path."""
    with open(path, "a"):
        os.utime(path, None)


def read_file(path: Path) -> str:
    """Read and return the contents of a file."""
    with open(path) as f:
        return f.read()


def write_file(path: Path, contents: str) -> None:
    """Write contents to a file."""
    with open(path, "w") as f:
        f.write(contents)


def _run_command(
    *command: str,
    **kwargs: Any,
) -> str:
    """Run a command and return its output."""
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        **kwargs,
    )
    stdout, _ = process.communicate()
    stdout = stdout.decode("utf-8")

    if process.returncode:
        raise Exception(stdout)  # noqa: TRY002

    return stdout


def run_hatch_command(
    *args: str,
    env: dict[str, str] | None = None,
) -> str:
    """
    Run a hatch command and return the result.

    Args:
        *args: Command arguments to pass to hatch
        env: Environment variables to use

    Returns:
        Command output as string
    """
    command_env = os.environ.copy()
    if env:
        command_env.update(env)

    result = _run_command(
        sys.executable,
        "-m",
        "hatch",
        *args,
        env=command_env,
    )

    return result


def run_in_hatch_env(
    env_name: str,
    command: str | list[str],
    env: dict[str, str] | None = None,
) -> str:
    """
    Run a command inside a specific Hatch environment.

    Args:
        env_name: Name of the Hatch environment
        command: Command to run (as a string or list)
        env: Environment variables

    Returns:
        CompletedProcess object
    """
    if isinstance(command, str):
        command = [command]

    command = [f"{env_name}:{command[0]}"] + command[1:]

    return run_hatch_command(
        "run",
        *command,
        env=env,
    )


def get_env_vars_in_hatch_env(
    var_names: list[str],
    env_name: str = "default",
    env: dict[str, str] | None = None,
) -> dict[str, str | None]:
    """
    Get the values of environment variables inside a Hatch environment.

    Args:
        env_name: Name of the Hatch environment
        var_names: List of variable names to get
        env: Environment variables

    Returns:
        Dictionary mapping variable names to their values (or None if not set)
    """
    # Ensure environment exists, otherwise we later have output
    # from the environment creation mixed in with our JSON output
    run_hatch_command(
        "env",
        "create",
        env_name,
    )

    # Create a Python command to print env vars as JSON
    var_names_str = ", ".join(f'"{v}"' for v in var_names)
    python_code = (
        f"import os, json; "
        # 4 curly braces reduce to 2 after f-string processing.
        # 2 curly braces are needed to escape when running the Hatch script
        # otherwise a single curly would be interpreted as Hatch context formatting
        # and result in the error: "Unknown context field `v`"
        # Unfortunately it is not documented very well, but here is a relevant issue:
        # -> https://github.com/pypa/hatch/issues/1198#issuecomment-1877333753
        #
        # To summarize, the below {{{{ x }}}} reduces to { x }
        f"print(json.dumps({{{{ v: os.environ.get(v) for v in [{var_names_str}] }}}}))"
    )
    command = [
        "python",
        "-c",
        python_code,
    ]
    result = run_in_hatch_env(
        env_name,
        command,
        env=env,
    )

    import json

    return json.loads(result.strip())


@contextmanager
def create_test_project(
    tmp_path: Path,
    pyproject_toml_content: str,
    extra_files: dict[str, str] | None = None,
) -> Generator[Path, None, None]:
    """
    Create a test Hatch project in a temporary directory.

    Args:
        tmp_path: Temporary directory path (from pytest fixture)
        pyproject_toml_content: Content for pyproject.toml
        extra_files: Dict of {path: content} for additional files to create

    Returns:
        Path to the created project directory
    """
    project_dir = tmp_path / "test_project"
    project_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Write pyproject.toml
    write_file(project_dir / "pyproject.toml", pyproject_toml_content)

    # Create a minimal package structure
    src_dir = project_dir / "src" / "test_package"
    src_dir.mkdir(
        parents=True,
        exist_ok=True,
    )
    write_file(src_dir / "__init__.py", "")

    # Create any additional files
    if extra_files:
        for file_path, content in extra_files.items():
            full_path = project_dir / file_path
            full_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )
            write_file(full_path, content)

    origin = Path.cwd()
    os.chdir(project_dir)
    try:
        yield project_dir
    finally:
        os.chdir(origin)
