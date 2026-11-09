from wattson_core.core.orchestrator import Orchestrator


class FakeConversation:
    def respond(self, message):
        return f"CONVERSA:{message}"


class FakeOpenCodeTool:
    def __init__(self):
        self.tasks = []

    def run(self, task):
        self.tasks.append(task)
        return f"OPENCODE:{task}"


def test_explicit_prefix_routes_to_opencode():
    tool = FakeOpenCodeTool()
    orchestrator = Orchestrator(FakeConversation(), opencode_tool=tool)

    result = orchestrator.handle("opencode: examine o projeto")

    assert result == "OPENCODE:examine o projeto"
    assert tool.tasks == ["examine o projeto"]


def test_normal_message_stays_in_conversation():
    tool = FakeOpenCodeTool()
    orchestrator = Orchestrator(FakeConversation(), opencode_tool=tool)

    result = orchestrator.handle("Olá Wattson")

    assert result == "CONVERSA:Olá Wattson"
    assert tool.tasks == []


def test_empty_opencode_task_is_rejected():
    tool = FakeOpenCodeTool()
    orchestrator = Orchestrator(FakeConversation(), opencode_tool=tool)

    result = orchestrator.handle("opencode:   ")

    assert "Informe uma tarefa" in result
    assert tool.tasks == []


def test_missing_opencode_tool_is_controlled():
    orchestrator = Orchestrator(FakeConversation())

    result = orchestrator.handle("opencode: analisar")

    assert "não configurada" in result


def test_opencode_failure_is_controlled():
    class FailingTool:
        def run(self, task):
            raise RuntimeError("falha simulada")

    orchestrator = Orchestrator(
        FakeConversation(),
        opencode_tool=FailingTool(),
    )

    result = orchestrator.handle("opencode: analisar")

    assert "falha simulada" in result


def test_opencode_os_error_is_controlled():
    class FailingTool:
        def run(self, task):
            raise OSError("opencode indisponível")

    orchestrator = Orchestrator(
        FakeConversation(),
        opencode_tool=FailingTool(),
    )

    result = orchestrator.handle("opencode: analisar")

    assert "Falha controlada no OpenCode" in result
    assert "opencode indisponível" in result
