import pytest

from wattson_core.ai.providers.openai_compatible import WattsonProvider


class FakeResponse:
    def __init__(self, data):
        self.data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self.data


def test_provider_generates_response(monkeypatch):
    monkeypatch.setenv("WATTSON_OPENAI_API_KEY", "test-key")

    def fake_post(url, headers, json, timeout):
        assert url == "https://api.example.test/v1/chat/completions"
        assert headers["Authorization"] == "Bearer test-key"
        assert json["model"] == "modelo-teste"
        assert json["messages"] == [
            {"role": "user", "content": "Olá, Wattson"}
        ]
        assert json["stream"] is False
        assert timeout == 120
        return FakeResponse({
            "choices": [
                {"message": {"content": "Resposta de teste."}}
            ]
        })

    monkeypatch.setattr(
        "wattson_core.ai.providers.openai_compatible.requests.post",
        fake_post,
    )

    provider = WattsonProvider(
        model="modelo-teste",
        base_url="https://api.example.test/v1/",
    )

    assert provider.generate("Olá, Wattson") == "Resposta de teste."


def test_provider_requires_api_key(monkeypatch):
    monkeypatch.delenv("WATTSON_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    provider = WattsonProvider(model="modelo-teste")

    with pytest.raises(RuntimeError, match="Chave ausente"):
        provider.generate("Teste")


def test_provider_rejects_invalid_response(monkeypatch):
    monkeypatch.setenv("WATTSON_OPENAI_API_KEY", "test-key")

    def fake_post(*args, **kwargs):
        return FakeResponse({"unexpected": "format"})

    monkeypatch.setattr(
        "wattson_core.ai.providers.openai_compatible.requests.post",
        fake_post,
    )

    provider = WattsonProvider(model="modelo-teste")

    with pytest.raises(ValueError, match="Resposta inválida"):
        provider.generate("Teste")


def test_provider_rejects_non_string_prompt():
    provider = WattsonProvider(
        model="modelo-teste",
        api_key="test-key",
    )

    with pytest.raises(TypeError, match="Prompt deve ser uma string"):
        provider.generate(None)
