import json
import os
from urllib.parse import urlencode
from urllib.request import urlopen


class SearchTool:
    BASE_URL = "http://127.0.0.1:8080/search"

    def __init__(self, base_url: str | None = None, timeout: float = 10):
        self.BASE_URL = (
            base_url
            or os.getenv("WATTSON_SEARCH_URL")
            or type(self).BASE_URL
        )
        self.timeout = timeout

    def search(self, query: str):
        if not isinstance(query, str) or not query.strip():
            raise ValueError("A consulta de pesquisa não pode estar vazia.")

        params = urlencode({
            "q": query.strip(),
            "format": "json",
        })

        with urlopen(
            f"{self.BASE_URL}?{params}",
            timeout=self.timeout,
        ) as response:
            data = json.load(response)

        if not isinstance(data, dict) or not isinstance(
            data.get("results"), list
        ):
            raise ValueError(
                "Resposta inválida do servidor de pesquisa: "
                "esperado um JSON com uma lista 'results'."
            )

        return data["results"]
