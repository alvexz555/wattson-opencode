import json
import subprocess
import sys
from pathlib import Path

import pytest

from wattson_core import mcp_server


class FakeOrchestrator:
    def __init__(self):
        self.messages = []
        self.diagnostic_formatter = self

    def handle(self, message):
        self.messages.append(message)
        return f"RESPOSTA:{message}"

    def run_diagnostic(self):
        return {"status": "OK"}

    def format(self, diagnostic):
        return f"DIAGNOSTICO:{diagnostic['status']}"


@pytest.fixture
def fake_orchestrator(monkeypatch):
    fake = FakeOrchestrator()
    monkeypatch.setattr(mcp_server, "_orchestrator", lambda: fake)
    return fake


def call(method, params=None, request_id=1):
    return mcp_server.handle_payload(
        {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params or {}}
    )


def test_initialize_announces_tools_capability():
    response = call("initialize", {"protocolVersion": "2024-11-05"})

    assert response["result"]["protocolVersion"] == "2024-11-05"
    assert "tools" in response["result"]["capabilities"]
    assert response["result"]["serverInfo"]["name"] == "wattson"


def test_tools_list_declares_chat_and_diagnose():
    tools = call("tools/list")["result"]["tools"]

    names = {tool["name"] for tool in tools}
    assert names == {"wattson_chat", "wattson_diagnose"}
    for tool in tools:
        assert tool["inputSchema"]["type"] == "object"


def test_chat_tool_routes_to_orchestrator(fake_orchestrator):
    response = call(
        "tools/call",
        {"name": "wattson_chat", "arguments": {"message": "  olá Wattson  "}},
    )

    assert response["result"]["isError"] is False
    assert response["result"]["content"][0]["text"] == "RESPOSTA:olá Wattson"
    assert fake_orchestrator.messages == ["olá Wattson"]


def test_diagnose_tool_returns_formatted_report(fake_orchestrator):
    response = call("tools/call", {"name": "wattson_diagnose", "arguments": {}})

    assert response["result"]["content"][0]["text"] == "DIAGNOSTICO:OK"
    assert response["result"]["isError"] is False


def test_empty_message_is_a_controlled_error(fake_orchestrator):
    response = call(
        "tools/call", {"name": "wattson_chat", "arguments": {"message": "  "}}
    )

    assert response["result"]["isError"] is True
    assert "message" in response["result"]["content"][0]["text"]


def test_unknown_tool_is_a_controlled_error(fake_orchestrator):
    response = call("tools/call", {"name": "nao_existe", "arguments": {}})

    assert response["result"]["isError"] is True


def test_unknown_method_returns_jsonrpc_error():
    response = call("metodo/inexistente")

    assert response["error"]["code"] == -32601


def test_initialized_notification_has_no_response():
    assert mcp_server.handle_payload(
        {"jsonrpc": "2.0", "method": "notifications/initialized"}
    ) is None


def test_stdio_server_speaks_jsonrpc_end_to_end():
    """Sobe o processo real como o OpenBot faz e usa o diagnóstico de verdade."""
    root = Path(__file__).resolve().parent.parent
    requests = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize",
         "params": {"protocolVersion": "2024-11-05", "capabilities": {}}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
         "params": {"name": "wattson_diagnose", "arguments": {}}},
    ]
    payload = "".join(json.dumps(item) + "\n" for item in requests)

    finished = subprocess.run(
        [sys.executable, "-m", "wattson_core.mcp_server"],
        input=payload,
        capture_output=True,
        text=True,
        cwd=root,
        timeout=90,
    )

    assert finished.returncode == 0, finished.stderr
    lines = [line for line in finished.stdout.splitlines() if line.strip()]
    assert len(lines) == 3  # a notificação não gera resposta

    responses = [json.loads(line) for line in lines]
    assert responses[0]["result"]["serverInfo"]["name"] == "wattson"
    assert {tool["name"] for tool in responses[1]["result"]["tools"]} == {
        "wattson_chat",
        "wattson_diagnose",
    }
    report = responses[2]["result"]["content"][0]["text"]
    assert "Diagnóstico concluído" in report
    assert responses[2]["result"]["isError"] is False
