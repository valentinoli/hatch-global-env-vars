# hatch-global-env-vars

| | |
| --- | --- |
| CI/CD | [![CI - Test](https://github.com/valentinoli/hatch-global-env-vars/actions/workflows/test.yml/badge.svg)](https://github.com/valentinoli/hatch-global-env-vars/actions/workflows/test.yml) [![CD - Build](https://github.com/valentinoli/hatch-global-env-vars/actions/workflows/build.yml/badge.svg)](https://github.com/valentinoli/hatch-global-env-vars/actions/workflows/build.yml) |
| Package | [![PyPI - Version](https://img.shields.io/pypi/v/hatch-global-env-vars.svg?logo=pypi&label=PyPI&logoColor=gold)](https://pypi.org/project/hatch-global-env-vars/) [![PyPI - Python Version](https://img.shields.io/pypi/pyversions/hatch-global-env-vars.svg?logo=python&label=Python&logoColor=gold)](https://pypi.org/project/hatch-global-env-vars/) |
| Meta | [![Hatch project](https://img.shields.io/badge/%F0%9F%A5%9A-Hatch-4051b5.svg)](https://github.com/pypa/hatch) [![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://docs.astral.sh/uv/) [![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://docs.astral.sh/ruff/) [![types - Mypy](https://img.shields.io/badge/types-Mypy-blue.svg)](https://mypy.readthedocs.io/en/stable/) [![License - MIT](https://img.shields.io/badge/license-MIT-9400d3.svg)](https://spdx.org/licenses/) |

-----

This provides an [environment collector plugin](https://hatch.pypa.io/latest/plugins/environment-collector/reference/) for [Hatch](https://hatch.pypa.io/latest) that sets global environment variables during Hatch initialization. This allows you to dynamically configure environment variables with conditional logic, variable copying, and recursive resolution.

**Key Feature:** Unlike Hatch's built-in `env-vars` which are scoped to individual environments, this plugin sets variables **globally using `os.environ`**, making them available to all environments and processes.

## Features

1. **Copy environment variables with fallback defaults**
2. **Optional variable copying** (only set if source exists)
3. **Conditional variable setting** based on environment state
4. **Recursive variable resolution** with dict syntax
5. **Global scope** - variables are set in `os.environ`, not just in Hatch environments

## Installation

- ***pyproject.toml***

    ```toml
    [tool.hatch.env]
    requires = ["hatch-global-env-vars"]
    ```

- ***hatch.toml***

    ```toml
    [env]
    requires = ["hatch-global-env-vars"]
    ```


## Usage

- ***pyproject.toml***

    ```toml
    [tool.hatch.env.collectors.global-env-vars]
    env-vars = [
        # ...
    ]
    ```

- ***hatch.toml***

    ```toml
    [env.collectors.global-env-vars]
    env-vars = [
        # ...
    ]
    ```

### Examples

```toml
[tool.hatch.env.collectors.global-env-vars]
env-vars = [
    # Example 1: Copy with fallback
    { name = "LOG_LEVEL", copy = "CI_LOG_LEVEL", default = "info" },

    # Example 2: Optional copy (only if source exists)
    { name = "API_KEY", copy = "SECRET_API_KEY", required = false },

    # Example 3: Existence check
    { name = "HAS_TOKEN", value = "yes", condition = "AUTH_TOKEN" },
    { name = "NO_TOKEN", value = "yes", condition = "!AUTH_TOKEN" },

    # Example 4: Empty/non-empty checks
    { name = "TOKEN_EMPTY", value = "true", condition = "AUTH_TOKEN==" },
    { name = "TOKEN_HAS_VALUE", value = "true", condition = "AUTH_TOKEN!=" },

    # Example 5: Value equality
    { name = "VERBOSE", value = "true", condition = "LOG_LEVEL==debug" },
    { name = "PROD_MODE", value = "true", condition = "ENVIRONMENT==production" },

    # Example 6: Value inequality
    { name = "NOT_PROD", value = "true", condition = "ENVIRONMENT!=production" },

    # Example 7: AND logic (all conditions must be true)
    { name = "DEPLOY", value = "true", condition = ["CI", "BRANCH==main", "DEPLOY_KEY"] },

    # Example 8: OR logic (any condition can be true)
    { name = "USE_CACHE", value = "redis", condition = { any = ["PROD", "STAGING"] } },

    # Example 9: Recursive resolution with variable reference dict
    { name = "APP_ENV", copy = "ENVIRONMENT", default = { name = "ENV", default = "development" } },

    # Example 10: Complex nested conditions
    { name = "FEATURE_X", value = "enabled", condition = { any = [
        { all = ["PROD", "FEATURE_FLAG==on"] },
        "FORCE_FEATURE_X"
    ] } },
]
```

## Configuration Options

Each entry in `env-vars` is a dictionary with these fields:

### Required Fields

- `name` (string): Name of the environment variable to set

### Variable Source (choose one)

- `copy` (string): Copy value from this environment variable
- `value` (string or dict): Set to this literal value or variable reference

### Optional Fields

- `default` (string or dict): Fallback value if `copy` source doesn't exist
  - Can be a literal string: `"development"`
  - Can be a variable reference dict: `{ name = "ENV", default = "dev" }`
  - Supports recursive nesting for fallback chains
- `required` (boolean): If `true` (default), raise error when `copy` source is missing and no `default` provided. If `false`, skip setting the variable when `copy` source is missing.
- `condition` (string, list, or dict): Only set the variable if this condition is true
  - **String conditions:**
    - `"ENV"`: true if ENV exists (regardless of value)
    - `"!ENV"`: true if ENV doesn't exist
    - `"ENV=="`: true if ENV exists and is empty string
    - `"ENV!="`: true if ENV exists and is non-empty
    - `"ENV==value"`: true if ENV equals value (value must be non-empty)
    - `"ENV!=value"`: true if ENV doesn't equal value
  - **List conditions (AND logic):** `["COND1", "COND2"]` - all must be true
  - **Dict conditions (OR logic):** `{ any = ["COND1", "COND2"] }` - at least one must be true
  - **Dict conditions (explicit AND):** `{ all = ["COND1", "COND2"] }` - all must be true

## Examples

### CI Detection

```toml
[tool.hatch.env.collectors.global-env-vars]
env-vars = [
    # Detect CI environment
    { name = "IS_CI", copy = "CI", default = "false" },

    # Set verbose logging in CI
    { name = "LOG_LEVEL", value = "debug", condition = "CI" },

    # Use different pytest args in CI
    { name = "PYTEST_ARGS", value = "-v --cov --cov-report=xml", condition = "CI" },
    { name = "PYTEST_ARGS", value = "-v", condition = "!CI" },

    # Only deploy from main branch in CI
    { name = "SHOULD_DEPLOY", value = "true", condition = ["CI", "BRANCH==main"] },

    # Require non-empty deploy key
    { name = "CAN_DEPLOY", value = "true", condition = ["CI", "BRANCH==main", "DEPLOY_KEY!="] },
]
```

### Multi-Environment Setup

```toml
[tool.hatch.env.collectors.global-env-vars]
env-vars = [
    # Copy environment with fallback chain using dict syntax
    { name = "APP_ENV", copy = "DEPLOY_ENV", default = { name = "ENVIRONMENT", default = "development" } },

    # Database URL based on environment
    { name = "DATABASE_URL", copy = "PROD_DATABASE_URL", condition = "ENVIRONMENT==production" },
    { name = "DATABASE_URL", copy = "STAGE_DATABASE_URL", condition = "ENVIRONMENT==staging" },
    { name = "DATABASE_URL", value = "sqlite:///dev.db", condition = { any = ["!ENVIRONMENT", "ENVIRONMENT==development"] } },

    # Config file with multiple fallbacks
    { name = "CONFIG_FILE", copy = "CUSTOM_CONFIG", default = { name = "ENV_CONFIG", default = "config/default.yaml" } },

    # Feature flags for prod or staging
    { name = "FEATURE_BETA", value = "enabled", condition = { any = ["ENVIRONMENT==production", "ENVIRONMENT==staging"] } },
]
```

### Secret Management

```toml
[tool.hatch.env.collectors.global-env-vars]
env-vars = [
    # Only set API key if secret exists (don't fail if missing)
    { name = "API_KEY", copy = "SECRET_API_KEY", required = false },

    # Use different key in CI
    { name = "API_KEY", copy = "CI_API_KEY", condition = "CI_API_KEY" },

    # Require authentication in production
    { name = "REQUIRE_AUTH", value = "true", condition = "ENVIRONMENT==production" },
    { name = "REQUIRE_AUTH", value = "false", condition = "ENVIRONMENT!=production" },

    # Only enable feature if token has a value (not empty)
    { name = "PREMIUM_FEATURES", value = "enabled", condition = "API_TOKEN!=" },
]
```

### Distinguishing Empty vs Non-existent Variables

```toml
[tool.hatch.env.collectors.global-env-vars]
env-vars = [
    # Check if TOKEN exists (regardless of value)
    { name = "TOKEN_SET", value = "true", condition = "TOKEN" },

    # Check if TOKEN doesn't exist
    { name = "NO_TOKEN", value = "true", condition = "!TOKEN" },

    # Check if TOKEN exists AND is empty string
    { name = "TOKEN_EMPTY", value = "true", condition = "TOKEN==" },

    # Check if TOKEN exists AND is non-empty
    { name = "TOKEN_HAS_VALUE", value = "true", condition = "TOKEN!=" },
]
```

**Truth table for different TOKEN states:**

| TOKEN state | `TOKEN` | `!TOKEN` | `TOKEN==` | `TOKEN!=` |
|-------------|---------|----------|-----------|-----------|
| Not set     | false   | **true** | false     | false     |
| Set to ""   | **true**| false    | **true**  | false     |
| Set to "x"  | **true**| false    | false     | **true**  |

## How It Works

This plugin implements a Hatch environment collector that runs during Hatch's initialization phase, **before any environments are created**.

The collector:
1. Reads configuration from `[tool.hatch.env.collectors.global-env-vars]`
2. Evaluates conditions to determine which variables to set
3. Resolves variable references recursively
4. **Sets variables globally in `os.environ`**, making them available to:
   - All Hatch environments (default, test, docs, etc.)
   - Child processes spawned by Hatch
   - Scripts run through Hatch

This is different from Hatch's built-in `env-vars` section, which only sets variables within specific environment scopes.

## Error Handling

The plugin will raise errors for:
- Missing required source variables (when `required=true` and no `default`)
- Invalid configuration (missing required fields, conflicting options)
- Circular references in recursive resolution

## License

`hatch-global-env-vars` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
