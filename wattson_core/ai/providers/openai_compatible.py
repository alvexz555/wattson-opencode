import os

import requests


class WattsonProvider:
    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
        api_key: str | None = None,
    ):
        self.model = (
            model
            or os.getenv("WATTSON_OPENAI_COMPATIBLE_MODEL")
            or "gpt-4o-mini"
        )

        self.base_url = (
            base_url
            or os.getenv(
                "WATTSON_OPENAI_COMPATIBLE_URL",
                "https://api.openai.com/v1",
            )
        ).rstrip("/")

        self.api_key = (
            api_key
            or os.getenv("WATTSON_OPENAI_API_KEY")
            or os.getenv("OPENAI_API_KEY")
        )

        if not self.model.strip():
            raise ValueError("O modelo não pode ser vazio.")

        if not self.base_url:
            raise ValueError("A URL da API não pode ser vazia.")

    def generate(self, prompt: str) -> str:
        if not isinstance(prompt, str):
            raise TypeError("Prompt deve ser uma string.")

        if not self.api_key:
            raise RuntimeError(
                "Chave ausente. Configure WATTSON_OPENAI_API_KEY "
                "ou OPENAI_API_KEY."
            )

        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "stream": False,
            },
            timeout=120,
        )

        response.raise_for_status()
        data = response.json()

        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as error:
            raise ValueError(
                "Resposta inválida da API compatível com OpenAI."
            ) from error

        if not isinstance(content, str):
            raise ValueError("A API não retornou texto na resposta.")

        return content
