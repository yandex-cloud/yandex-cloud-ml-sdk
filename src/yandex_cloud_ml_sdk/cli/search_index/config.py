from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import click

from yandex_cloud_ml_sdk.auth import APIKeyAuth, IAMTokenAuth, MetadataAuth, OAuthTokenAuth, YandexCloudCLIAuth

logger = logging.getLogger(__name__)


class ConfigLoader:
    """Loader for YAML and JSON configuration files."""

    @staticmethod
    def load(config_path: Path) -> dict[str, Any]:
        if not config_path.exists():
            raise click.ClickException(f"Configuration file not found: {config_path}")

        suffix = config_path.suffix.lower()

        try:
            if suffix in (".yaml", ".yml"):
                return ConfigLoader._load_yaml(config_path)
            elif suffix == ".json":
                return ConfigLoader._load_json(config_path)
            else:
                raise click.ClickException(
                    f"Unsupported format: {suffix}. Use .yaml, .yml, or .json"
                )
        except Exception as e:
            if isinstance(e, click.ClickException):
                raise
            raise click.ClickException(f"Error loading config: {e}")

    @staticmethod
    def _load_yaml(config_path: Path) -> dict[str, Any]:
        try:
            import yaml
        except ImportError:
            raise click.ClickException(
                "PyYAML required for YAML configs. Install: pip install pyyaml"
            )

        with open(config_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)

        if config is None:
            return {}

        if not isinstance(config, dict):
            raise click.ClickException("Config must be a dictionary")

        return config

    @staticmethod
    def _load_json(config_path: Path) -> dict[str, Any]:
        with open(config_path, encoding="utf-8") as f:
            config = json.load(f)

        if not isinstance(config, dict):
            raise click.ClickException("Config must be a JSON object")

        return config


def extract_source_config(config: dict[str, Any], source_name: str) -> dict[str, Any]:
    """
    Extract source-specific configuration from config file.

    Looks for a section named after the source (e.g., 'local', 's3', 'wiki', 'confluence')
    and merges it with common/global config. Source-specific values take precedence.
    """
    result = {}

    for key, value in config.items():
        if key in ("local", "s3", "wiki", "confluence"):
            continue
        result[key] = value

    if source_name in config and isinstance(config[source_name], dict):
        source_config = config[source_name]
        for key, value in source_config.items():
            result[key] = value
            logger.debug("Using '%s' from [%s] section", key, source_name)

    return result


def filter_null_values(config: dict[str, Any]) -> dict[str, Any]:
    """Remove keys with None/null values from config."""
    return {k: v for k, v in config.items() if v is not None}


def add_default_values(config: dict[str, Any], source_name: str) -> dict[str, Any]:
    """Add default values for missing parameters based on source type."""
    result = config.copy()

    # Common defaults for all commands
    common_defaults = {
        "endpoint": None,
        "metadata": (),
        "expires_after_days": None,
        "expires_after_anchor": None,
        "file_purpose": "assistants",
        "file_expires_after_seconds": None,
        "file_expires_after_anchor": None,
        "max_concurrent_uploads": 5,
        "skip_on_error": True,
        "output_format": "text",
    }
    for key, default_value in common_defaults.items():
        if key not in result:
            result[key] = default_value

    # Source-specific defaults
    defaults: dict[str, Any]
    if source_name == "wiki":
        defaults = {
            "username": None,
            "password": None,
            "page_titles": (),
            "category": None,
            "export_format": "text",
        }
        for key, default_value in defaults.items():
            if key not in result:
                result[key] = default_value

    elif source_name == "confluence":
        defaults = {
            "base_url": None,
            "username": None,
            "api_token": None,
            "export_format": "pdf",
        }
        for key, default_value in defaults.items():
            if key not in result:
                result[key] = default_value

    elif source_name == "s3":
        defaults = {
            "prefix": "",
            "endpoint_url": None,
            "aws_access_key_id": None,
            "aws_secret_access_key": None,
            "region_name": None,
            "include_patterns": (),
            "exclude_patterns": (),
            "max_file_size": None,
        }
        for key, default_value in defaults.items():
            if key not in result:
                result[key] = default_value

    elif source_name == "local":
        defaults = {
            "exclude_patterns": (),
            "max_file_size": None,
        }
        for key, default_value in defaults.items():
            if key not in result:
                result[key] = default_value

    return result


def normalize_list_params(config: dict[str, Any]) -> dict[str, Any]:
    """Convert list parameters to tuples for CLI compatibility.

    CLI uses tuples for multiple-value options, but configs use lists.
    Convert lists to tuples for compatibility with Click commands.
    Also normalize parameter names (singular -> plural).
    """
    result = config.copy()

    # Map singular to plural forms
    param_mappings = {
        "page_url": "page_urls",
        "pattern": "include_patterns",
        "exclude_pattern": "exclude_patterns",
        "include_pattern": "include_patterns",
    }

    # First apply mappings
    for singular, plural in param_mappings.items():
        if singular in result:
            result[plural] = result.pop(singular)

    # Then convert lists to tuples
    list_params = {
        "metadata",
        "exclude_patterns",
        "include_patterns",
        "page_urls",
    }

    for key in list_params:
        if key in result and isinstance(result[key], list):
            result[key] = tuple(result[key])

    return result


def merge_config_with_cli_args(config: dict[str, Any], cli_args: dict[str, Any]) -> dict[str, Any]:
    """Merge config file with CLI args. CLI args take precedence."""
    merged = config.copy()

    for key, value in cli_args.items():
        if value is None:
            continue

        if isinstance(value, tuple) and len(value) == 0:
            continue

        merged[key] = value
        logger.debug("CLI arg '%s' overrides config", key)

    return merged


def normalize_config_keys(config: dict[str, Any]) -> dict[str, Any]:
    """Convert kebab-case to snake_case (folder-id -> folder_id)."""
    normalized = {}
    for key, value in config.items():
        normalized_key = key.replace("-", "_")

        if isinstance(value, dict) and key in ("local", "s3", "wiki", "confluence"):
            normalized[normalized_key] = {k.replace("-", "_"): v for k, v in value.items()}
        else:
            normalized[normalized_key] = value

    return normalized


def parse_auth_config(config: dict[str, Any]) -> dict[str, Any]:
    """
    Parse auth configuration and create appropriate auth object.

    Supports:
    - api_key: Creates APIKeyAuth
    - iam_token: Creates IAMTokenAuth
    - oauth_token: Creates OAuthTokenAuth
    - metadata: true - Creates MetadataAuth
    - yc_cli: true - Creates YandexCloudCLIAuth
    - auth: string - Keep as-is (legacy)
    """
    result = config.copy()

    if "auth" in result and isinstance(result["auth"], str):
        return result

    auth_obj: APIKeyAuth | IAMTokenAuth | OAuthTokenAuth | MetadataAuth | YandexCloudCLIAuth | None = None

    if "api_key" in result:
        auth_obj = APIKeyAuth(api_key=result.pop("api_key"))
    elif "iam_token" in result:
        auth_obj = IAMTokenAuth(token=result.pop("iam_token"))
    elif "oauth_token" in result:
        auth_obj = OAuthTokenAuth(token=result.pop("oauth_token"))
    elif result.get("metadata") is True:
        auth_obj = MetadataAuth()
        result.pop("metadata")
    elif result.get("yc_cli") is True:
        auth_obj = YandexCloudCLIAuth()
        result.pop("yc_cli")

    if auth_obj:
        result["auth"] = auth_obj

    return result
