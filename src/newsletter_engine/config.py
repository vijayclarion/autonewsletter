"""Configuration loading and validation.

Configuration is the only place provider identity, routing, thresholds, brand, and
policies live (constitution I, VII, IX; FR-027). Secrets come from environment variables
only. A role referencing a provider absent from the allow-list aborts startup (fail fast).
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

# Providers that never send content off the machine; always permitted (FR-027).
LOCAL_PROVIDERS = ("local", "mock")


class ConfigError(Exception):
    """Invalid or missing configuration; startup must abort."""


@dataclass
class ClassifierConfig:
    confidence_threshold: float = 0.8


@dataclass
class DiagramConfig:
    max_regeneration_retries: int = 2


@dataclass
class RoleRoute:
    provider: str
    model: str


@dataclass
class ProviderConfig:
    api_key_env: str | None = None


@dataclass
class ModelsConfig:
    allowlist: list[str]
    providers: dict[str, ProviderConfig]
    roles: dict[str, RoleRoute]
    pricing: dict[str, dict[str, float]]


@dataclass
class BrandConfig:
    newsletter_title: str = "Engineering Insights"
    logo_path: str | None = None
    palette: dict[str, str] = field(default_factory=dict)
    typography: dict[str, str] = field(default_factory=dict)
    pending_brand_assets: bool = True


@dataclass
class RedactionConfig:
    emails: bool = True
    phone_numbers: bool = True
    custom_patterns: list[str] = field(default_factory=list)
    speaker_handling: str = "role"
    role_map: dict[str, str] = field(default_factory=dict)
    default_speaker_role: str = "Team Member"


REQUIRED_ROLES = ("classifier", "writer", "diagrammer", "embedder")


@dataclass
class AppConfig:
    root_dir: Path          # project root all relative paths resolve against
    config_dir: Path
    source_dir: Path
    output_dir: Path
    archive_dir: Path
    classification_default: str
    classifier: ClassifierConfig
    diagrams: DiagramConfig
    models: ModelsConfig
    brand: BrandConfig
    redaction: RedactionConfig


def _read_yaml(path: Path) -> dict:
    if not path.exists():
        raise ConfigError(f"Missing configuration file: {path}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigError(f"Invalid YAML in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigError(f"Configuration file {path} must contain a mapping")
    return data


def _load_models(path: Path) -> ModelsConfig:
    raw = _read_yaml(path)
    allowlist = raw.get("allowlist") or []
    if not allowlist:
        raise ConfigError(f"{path}: 'allowlist' must list at least one provider")

    providers = {
        name: ProviderConfig(api_key_env=(spec or {}).get("api_key_env"))
        for name, spec in (raw.get("providers") or {}).items()
    }

    roles: dict[str, RoleRoute] = {}
    for role, spec in (raw.get("roles") or {}).items():
        if not isinstance(spec, dict) or "provider" not in spec or "model" not in spec:
            raise ConfigError(f"{path}: role '{role}' needs 'provider' and 'model'")
        roles[role] = RoleRoute(provider=spec["provider"], model=spec["model"])

    for role in REQUIRED_ROLES:
        if role not in roles:
            raise ConfigError(f"{path}: required role '{role}' is not configured")

    # Fail-fast allow-list rule (FR-027): no role may route to a non-allow-listed remote
    # provider. Local providers never send content off the machine and are always allowed.
    for role, route in roles.items():
        if route.provider in LOCAL_PROVIDERS:
            continue
        if route.provider not in allowlist:
            raise ConfigError(
                f"{path}: role '{role}' routes to provider '{route.provider}' "
                f"which is not in the allowlist {allowlist}"
            )
        if route.provider not in providers:
            raise ConfigError(
                f"{path}: role '{role}' routes to provider '{route.provider}' "
                "which has no entry under 'providers'"
            )

    pricing = raw.get("pricing") or {}
    return ModelsConfig(allowlist=allowlist, providers=providers, roles=roles, pricing=pricing)


def _load_brand(path: Path) -> BrandConfig:
    raw = _read_yaml(path)
    return BrandConfig(
        newsletter_title=raw.get("newsletter_title", "Engineering Insights"),
        logo_path=raw.get("logo_path"),
        palette=raw.get("palette") or {},
        typography=raw.get("typography") or {},
        pending_brand_assets=bool(raw.get("pending_brand_assets", True)),
    )


def _load_redaction(path: Path) -> RedactionConfig:
    raw = _read_yaml(path)
    redact = raw.get("redact") or {}
    role_map = raw.get("role_map") or {}
    # Drop the empty-key placeholder some templates carry.
    role_map = {k: v for k, v in role_map.items() if k}
    return RedactionConfig(
        emails=bool(redact.get("emails", True)),
        phone_numbers=bool(redact.get("phone_numbers", True)),
        custom_patterns=list(redact.get("custom_patterns") or []),
        speaker_handling=raw.get("speaker_handling", "role"),
        role_map=role_map,
        default_speaker_role=raw.get("default_speaker_role", "Team Member"),
    )


# env var -> producer-supplied, git-ignored key file at the repo root (research R13)
_KEY_FILE_FALLBACKS = {
    "ANTHROPIC_API_KEY": "claudeapi-key.txt",
    "OPENAI_API_KEY": "openai-key.txt",
}


def load_key_fallbacks(root_dir: Path) -> None:
    """Producer-supplied key fallback (research R13).

    If a provider's key env var is not set but its git-ignored key file exists at the
    repo root, load the key from it and warn the producer to migrate it to ``.env``.
    The key value itself is never logged or written anywhere.
    """
    for env_var, filename in _KEY_FILE_FALLBACKS.items():
        if os.environ.get(env_var):
            continue
        key_file = root_dir / filename
        if not key_file.exists():
            continue
        key = key_file.read_text(encoding="utf-8").strip()
        if not key:
            continue
        os.environ[env_var] = key
        print(
            f"WARNING: loaded {env_var} from {filename} (git-ignored);"
            " move the key into .env and delete the file.",
            file=sys.stderr,
        )


def load_config(config_path: str | Path = "config/config.yaml") -> AppConfig:
    """Load the configuration root plus its sibling files, validating everything up front."""
    config_file = Path(config_path).resolve()
    raw = _read_yaml(config_file)
    config_dir = config_file.parent
    root_dir = config_dir.parent

    classifier_raw = raw.get("classifier") or {}
    threshold = float(classifier_raw.get("confidence_threshold", 0.8))
    if not 0.0 <= threshold <= 1.0:
        raise ConfigError(f"classifier.confidence_threshold must be in [0, 1], got {threshold}")

    diagrams_raw = raw.get("diagrams") or {}
    retries = int(diagrams_raw.get("max_regeneration_retries", 2))
    if retries < 0:
        raise ConfigError("diagrams.max_regeneration_retries must be >= 0")

    classification_default = raw.get("classification_default", "internal")
    if classification_default not in ("public", "internal", "confidential"):
        raise ConfigError(
            f"classification_default must be public|internal|confidential, "
            f"got '{classification_default}'"
        )

    def _resolve(value: str) -> Path:
        p = Path(value)
        return p if p.is_absolute() else root_dir / p

    return AppConfig(
        root_dir=root_dir,
        config_dir=config_dir,
        source_dir=_resolve(raw.get("source_dir", "Documents")),
        output_dir=_resolve(raw.get("output_dir", "editions")),
        archive_dir=_resolve(raw.get("archive_dir", "archive")),
        classification_default=classification_default,
        classifier=ClassifierConfig(confidence_threshold=threshold),
        diagrams=DiagramConfig(max_regeneration_retries=retries),
        models=_load_models(config_dir / "models.yaml"),
        brand=_load_brand(config_dir / "brand.yaml"),
        redaction=_load_redaction(config_dir / "redaction.yaml"),
    )
