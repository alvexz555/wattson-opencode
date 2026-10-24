import pytest

from wattson_core.ai.providers.ollama import WattsonProvider


class FakeResponse:
    def __init__(self, data):
        self.data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self.data


def test_wattson_provider_generates_response(monkeypatch):
    expected = "Resposta do Dolphin."

    def fake_post(url, json, timeout):
        assert "dolphin-llama3:8b" in json["model"]
        assert json["prompt"] == "Olá, Wattson"
        return FakeResponse({"response": expected})

    monkeypatch.setattr(
        "wattson_core.ai.providers.ollama.requests.post",
        fake_post,
    )

    provider = WattsonProvider(model="dolphin-llama3:8b")

    result = provider.generate("Olá, Wattson")

    assert result == expected
