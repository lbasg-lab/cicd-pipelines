import pytest

from scripts.validate_config import (
    ConfigurationError,
    validate_config,
    validate_schema,
)


def valid_config():
    return {
        "version": 1,
        "runtime": {
            "stack": "node",
            "version": "24",
            "package_manager": "npm",
        },
    }


@pytest.mark.parametrize("version", ["22", "24"])
def test_supported_node_version(version):
    config = valid_config()
    config["runtime"]["version"] = version

    validate_config(config)


def test_unsupported_node_version():
    config = valid_config()
    config["runtime"]["version"] = "20"

    with pytest.raises(
        ConfigurationError,
        match="Unsupported Node.js version: 20",
    ):
        validate_config(config)


def test_unsupported_node_current_version():
    config = valid_config()
    config["runtime"]["version"] = "26"

    with pytest.raises(
        ConfigurationError,
        match="Unsupported Node.js version: 26",
    ):
        validate_config(config)


def test_unsupported_stack():
    config = valid_config()
    config["runtime"]["stack"] = "python"

    with pytest.raises(
        ConfigurationError,
        match="Unsupported runtime stack: python",
    ):
        validate_config(config)


def test_unsupported_package_manager():
    config = valid_config()
    config["runtime"]["package_manager"] = "pnpm"

    with pytest.raises(
        ConfigurationError,
        match="Unsupported package manager for Node.js: pnpm",
    ):
        validate_config(config)


def test_invalid_configuration_version():
    config = valid_config()
    config["version"] = 2

    with pytest.raises(
        ConfigurationError,
        match="Unsupported configuration version",
    ):
        validate_config(config)


def test_schema_requires_version():
    config = valid_config()
    del config["version"]

    with pytest.raises(ConfigurationError, match="Schema validation failed"):
        validate_schema(config)


def test_schema_requires_runtime():
    config = valid_config()
    del config["runtime"]

    with pytest.raises(ConfigurationError, match="Schema validation failed"):
        validate_schema(config)


def test_schema_rejects_unknown_top_level_property():
    config = valid_config()
    config["project"] = "example"

    with pytest.raises(ConfigurationError, match="Schema validation failed"):
        validate_schema(config)


def test_schema_rejects_unknown_runtime_property():
    config = valid_config()
    config["runtime"]["node_version"] = "24"

    with pytest.raises(ConfigurationError, match="Schema validation failed"):
        validate_schema(config)
