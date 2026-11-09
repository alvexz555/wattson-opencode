"""Servidor MCP local que expõe o Wattson ao OpenBot.

Fala JSON-RPC 2.0 por stdio (uma mensagem JSON por linha), sem dependências
externas. O OpenBot inicia este processo e passa a ver as ferramentas
declaradas em ``TOOLS``.
"""
from __future__ import annotations

import json
import sys
from typing import Any

PROTOCOL_VERSION = "2024-11-05"
SERVER_INFO = {"name": "wattson", "version": "0.1.0"}

TOOLS: list[dict[str, Any]] = [
    {
        "name": "wattson_chat",
        "description": (
            "Envia uma mensagem ao Wattson Core e devolve a resposta dele. "
            "O Wattson roteia sozinho entre conversa, diagnóstico, busca e "
            "tarefas 'opencode:'."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Mensagem ou pedido para o Wattson.",
                }
            },
            "required": ["message"],
            "additionalProperties": False,
        },
    },
    {
        "name": "wattson_diagnose",
        "description": (
            "Executa a autoavaliação ADR0 do Wattson e devolve o relatório "
            "formatado (status, verificações que passaram e falhas)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
]


def _orchestrator():
    """Constrói o Orchestrator na primeira chamada.

    Adia a inicialização para que o servidor responda ao handshake MCP mesmo
    quando o provider de IA ainda não está configurado.
    """
    from wattson_core.terminal_runner import create_orchestrator

    return create_orchestrator()


def call_tool(name: str, arguments: dict[str, Any] | None) -> str:
    arguments = arguments or {}

    if name == "wattson_chat":
        message = arguments.get("message")
        if not isinstance(message, str) or not message.strip():
            raise ValueError("O campo 'message' é obrigatório.")
        return _orchestrator().handle(message.strip())

    if name == "wattson_diagnose":
        orchestrator = _orchestrator()
        diagnostic = orchestrator.run_diagnostic()
        return orchestrator.diagnostic_formatter.format(diagnostic)

    raise KeyError(f"Ferramenta desconhecida: {name}")


def _result(request_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _error(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": code, "message": message},
    }


def _tool_response(text: str, is_error: bool = False) -> dict[str, Any]:
    return {
        "content": [{"type": "text", "text": text}],
        "isError": is_error,
    }


def handle_payload(payload: dict[str, Any]) -> dict[str, Any] | None:
    """Processa uma mensagem JSON-RPC e devolve a resposta (ou None)."""
    if not isinstance(payload, dict):
        return _error(None, -32600, "Requisição inválida.")

    method = payload.get("method")
    request_id = payload.get("id")
    params = payload.get("params") or {}

    if method == "initialize":
        requested = params.get("protocolVersion")
        version = requested if isinstance(requested, str) else PROTOCOL_VERSION
        return _result(
            request_id,
            {
                "protocolVersion": version,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": SERVER_INFO,
            },
        )

    if method in ("notifications/initialized", "initialized"):
        return None

    if method == "ping":
        return _result(request_id, {})

    if method == "tools/list":
        return _result(request_id, {"tools": TOOLS})

    if method == "resources/list":
        return _result(request_id, {"resources": []})

    if method == "prompts/list":
        return _result(request_id, {"prompts": []})

    if method == "tools/call":
        name = params.get("name")
        arguments = params.get("arguments")
        try:
            text = call_tool(name, arguments)
        except KeyError as exc:
            return _result(
                request_id,
                _tool_response(str(exc).strip("'\""), is_error=True),
            )
        except Exception as exc:  # falha controlada, nunca derruba o servidor
            return _result(
                request_id,
                _tool_response(f"{type(exc).__name__}: {exc}", is_error=True),
            )
        return _result(request_id, _tool_response(text))

    if method is None:
        return _error(request_id, -32600, "Método ausente.")

    return _error(request_id, -32601, f"Método desconhecido: {method}")


def serve(stdin=None, stdout=None) -> None:
    stdin = stdin or sys.stdin
    stdout = stdout or sys.stdout

    for line in stdin:
        line = line.strip()
        if not line:
            continue

        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            stdout.write(json.dumps(_error(None, -32700, "JSON inválido.")) + "\n")
            stdout.flush()
            continue

        response = handle_payload(payload)
        if response is not None:
            stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
            stdout.flush()


def main() -> int:
    try:
        serve()
    except KeyboardInterrupt:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
