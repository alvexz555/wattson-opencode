import pytest

from wattson_core.ai import registry


def test_registry_uses_ollama_by_default(monkeypatch):
    monkeypatch.delenv("WATTSON_PROVIDER", raising=False)
    assert registry.load().__name__ == "wattson_core.ai.providers.ollama"


def test_registry_uses_environment_provider(monkeypatch):
    monkeypatch.setenv("WATTSON_PROVIDER", "ollama")
    assert registry.load().__name__ == "wattson_core.ai.providers.ollama"


def test_registry_rejects_invalid_provider_name():
    with pytest.raises(ValueError, match="Nome de provider inválido"):
        registry.load("../ollama")


def test_registry_returns_none_for_unknown_provider():
    assert registry.load("provider_que_nao_existe") is None
