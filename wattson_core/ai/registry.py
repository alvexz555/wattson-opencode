import importlib
import os
import re


def load(name: str | None = None):
    provider_name = name or os.getenv("WATTSON_PROVIDER", "ollama")
    provider_name = provider_name.strip().lower()

    if not re.fullmatch(r"[a-z][a-z0-9_]*", provider_name):
        raise ValueError(f"Nome de provider inválido: {provider_name!r}")

    try:
        return importlib.import_module(
            f"wattson_core.ai.providers.{provider_name}"
        )
    except ModuleNotFoundError as error:
        expected_module = f"wattson_core.ai.providers.{provider_name}"
        if error.name == expected_module:
            return None
        raise
