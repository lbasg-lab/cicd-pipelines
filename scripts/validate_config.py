#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator


SUPPORTED_STACKS = {"node"}
SUPPORTED_NODE_VERSIONS = {"22", "24"}
SUPPORTED_NODE_PACKAGE_MANAGERS = {"npm"}

SCRIPT_DIR = Path(__file__).resolve().parent
REPOSITORY_ROOT = SCRIPT_DIR.parent
SCHEMA_PATH = REPOSITORY_ROOT / "schemas" / "cicd-config.schema.json"


class ConfigurationError(Exception):
    """Raised when the CI/CD configuration is invalid."""


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        description="Validate a lbasg-lab CI/CD configuration."
    )

    parser.add_argument(
        "config",
        type=Path,
        help="Path to the CI/CD configuration file.",
    )

    parser.add_argument(
        "--github-output",
        type=Path,
        help="GitHub Actions output file.",
    )

    return parser.parse_args()


def load_config(config_path: Path) -> dict:
    """Load and parse the YAML configuration file."""

    if not config_path.is_file():
        raise ConfigurationError(
            f"Configuration file not found: {config_path}"
        )

    try:
        with config_path.open("r", encoding="utf-8") as file:
            config = yaml.safe_load(file)
    except yaml.YAMLError as exc:
        raise ConfigurationError(
            f"Invalid YAML syntax: {exc}"
        ) from exc

    if not isinstance(config, dict):
        raise ConfigurationError(
            "Configuration must contain a YAML object."
        )

    return config


def load_schema() -> dict:
    """Load the JSON Schema used to validate the configuration."""

    if not SCHEMA_PATH.is_file():
        raise ConfigurationError(
            f"Schema file not found: {SCHEMA_PATH}"
        )

    try:
        with SCHEMA_PATH.open("r", encoding="utf-8") as file:
            schema = yaml.safe_load(file)
    except yaml.YAMLError as exc:
        raise ConfigurationError(
            f"Invalid schema syntax: {exc}"
        ) from exc

    if not isinstance(schema, dict):
        raise ConfigurationError(
            "Schema must contain a JSON object."
        )

    return schema


def validate_schema(config: dict) -> None:
    """Validate the configuration structure against the JSON Schema."""

    schema = load_schema()

    validator = Draft202012Validator(schema)
    errors = sorted(
        validator.iter_errors(config),
        key=lambda error: list(error.absolute_path),
    )

    if not errors:
        return

    error = errors[0]

    path = ".".join(str(part) for part in error.absolute_path)

    if path:
        raise ConfigurationError(
            f"Schema validation failed at '{path}': {error.message}"
        )

    raise ConfigurationError(
        f"Schema validation failed: {error.message}"
    )


def validate_config(config: dict) -> None:
    """Validate framework-specific configuration rules."""

    if config.get("version") != 1:
        raise ConfigurationError(
            "Unsupported configuration version. "
            "Supported version: 1"
        )

    runtime = config.get("runtime")

    if not isinstance(runtime, dict):
        raise ConfigurationError(
            "Missing or invalid 'runtime' configuration."
        )

    stack = runtime.get("stack")

    if stack not in SUPPORTED_STACKS:
        supported = ", ".join(sorted(SUPPORTED_STACKS))

        raise ConfigurationError(
            f"Unsupported runtime stack: {stack}\n"
            f"Supported stacks: {supported}"
        )

    if stack == "node":
        validate_node_runtime(runtime)


def validate_node_runtime(runtime: dict) -> None:
    """Validate Node.js-specific configuration rules."""

    version = runtime.get("version")

    if version is None:
        raise ConfigurationError(
            "Missing required runtime version for Node.js."
        )

    version = str(version)

    if version not in SUPPORTED_NODE_VERSIONS:
        supported = ", ".join(sorted(SUPPORTED_NODE_VERSIONS))

        raise ConfigurationError(
            f"Unsupported Node.js version: {version}\n"
            f"Supported versions: {supported}"
        )

    package_manager = runtime.get("package_manager")

    if package_manager not in SUPPORTED_NODE_PACKAGE_MANAGERS:
        supported = ", ".join(
            sorted(SUPPORTED_NODE_PACKAGE_MANAGERS)
        )

        raise ConfigurationError(
            f"Unsupported package manager for Node.js: "
            f"{package_manager}\n"
            f"Supported package managers: {supported}"
        )


def write_github_outputs(
    config: dict,
    output_path: Path,
) -> None:
    """Write validated configuration values to GitHub Actions outputs."""

    runtime = config["runtime"]

    outputs = {
        "runtime_stack": runtime["stack"],
        "runtime_version": str(runtime["version"]),
        "package_manager": runtime["package_manager"],
    }

    with output_path.open("a", encoding="utf-8") as file:
        for name, value in outputs.items():
            file.write(f"{name}={value}\n")


def main() -> int:
    """Run configuration validation."""

    args = parse_arguments()

    try:
        config = load_config(args.config)
        validate_schema(config)
        validate_config(config)

        if args.github_output:
            write_github_outputs(config, args.github_output)

    except ConfigurationError as exc:
        print("✗ Configuration error", file=sys.stderr)
        print(file=sys.stderr)
        print(exc, file=sys.stderr)
        return 1

    print("✓ Configuration is valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
