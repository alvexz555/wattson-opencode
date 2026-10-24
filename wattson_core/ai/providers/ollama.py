import os

import requests


class WattsonProvider:
    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
    ):
        self.model = model or os.getenv(
            "WATTSON_MODEL",
            "gemma4:e2b",
        )

        self.base_url = (
            base_url
            or os.getenv(
                "WATTSON_OLLAMA_URL",
                "http://localhost:11434",
            )
        ).rstrip("/")

        if not self.model.strip():
            raise ValueError("WATTSON_MODEL não pode ser vazio")

    def generate(self, prompt: str) -> str:
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
            },
            timeout=120,
        )

        response.raise_for_status()
        data = response.json()

        return data["response"]
