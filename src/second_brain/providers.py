"""LLM provider health checks with no provider-specific runtime paths."""
from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass

from .config import LLMConfig


@dataclass(frozen=True)
class Health:
    ok: bool
    detail: str


DEFAULT_ENDPOINTS = {
    "ollama": "http://127.0.0.1:11434",
    "lm-studio": "http://127.0.0.1:1234",
    "openai": "https://api.openai.com",
    "anthropic": "https://api.anthropic.com",
}


def endpoint_for(config: LLMConfig) -> str:
    return (config.endpoint or DEFAULT_ENDPOINTS.get(config.provider, "")).rstrip("/")


def healthcheck(config: LLMConfig, secret: str = "") -> Health:
    endpoint = endpoint_for(config)
    if config.provider == "anthropic":
        return Health(bool(secret), "API key configured" if secret else "Anthropic API key is missing")
    if config.provider in {"openai", "openai-compatible", "lm-studio"}:
        url = f"{endpoint}/v1/models"
    elif config.provider == "ollama":
        url = f"{endpoint}/api/tags"
    else:
        return Health(False, "unknown provider")
    request = urllib.request.Request(url)
    if secret and config.provider in {"openai", "openai-compatible"}:
        request.add_header("Authorization", f"Bearer {secret}")
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            json.load(response)
        return Health(True, f"reachable: {endpoint}")
    except Exception as exc:
        return Health(False, f"unreachable: {endpoint} ({exc})")
