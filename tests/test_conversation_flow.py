from wattson_core.ai.conversation import ConversationAI
from wattson_core.ai.context import ConversationContext
from wattson_core.ai.engine import AIEngine
from wattson_core.core.orchestrator import Orchestrator


def test_full_conversation_flow():
    class FakeProvider:
        def generate(self, prompt: str) -> str:
            return f"Wattson recebeu: {prompt}"

    provider = FakeProvider()
    engine = AIEngine(provider)
    context = ConversationContext()
    conversation = ConversationAI(engine, context)
    orchestrator = Orchestrator(conversation)

    result = orchestrator.handle("Olá, Wattson")

    assert result.startswith("Wattson recebeu: Você é Wattson")
    assert "Usuário: Olá, Wattson" in result
    assert "Olá, Wattson" in context.messages


def test_conversation_preserves_history():
    class FakeProvider:
        def __init__(self):
            self.prompts = []

        def generate(self, prompt: str) -> str:
            self.prompts.append(prompt)
            return "resposta"

    provider = FakeProvider()
    engine = AIEngine(provider)
    context = ConversationContext()
    conversation = ConversationAI(engine, context)
    orchestrator = Orchestrator(conversation)

    orchestrator.handle("Meu nome é A.RISE.")
    orchestrator.handle("Qual é o meu nome?")

    assert len(provider.prompts) == 2
    assert "Usuário: Meu nome é A.RISE." in provider.prompts[1]
    assert "Wattson: resposta" in provider.prompts[1]
    assert "Usuário: Qual é o meu nome?" in provider.prompts[1]


def test_conversation_sessions_are_independent():
    class FakeProvider:
        def generate(self, prompt: str) -> str:
            return "resposta"

    provider = FakeProvider()
    engine = AIEngine(provider)
    first_context = ConversationContext()
    second_context = ConversationContext()
    first_conversation = ConversationAI(engine, first_context)
    second_conversation = ConversationAI(engine, second_context)
    first_orchestrator = Orchestrator(first_conversation)
    second_orchestrator = Orchestrator(second_conversation)

    first_orchestrator.handle("Segredo da primeira sessão.")
    second_orchestrator.handle("Mensagem da segunda sessão.")

    assert "Segredo da primeira sessão." in first_context.messages
    assert "Segredo da primeira sessão." not in second_context.messages
    assert "Mensagem da segunda sessão." in second_context.messages


def test_closed_session_rejects_conversation_message():
    from wattson_core.ai.session import Session

    class FakeProvider:
        def generate(self, prompt: str) -> str:
            return "resposta"

    engine = AIEngine(FakeProvider())
    session = Session()
    conversation = ConversationAI(engine, session.context)
    orchestrator = Orchestrator(conversation)
    session.close()

    try:
        session.add_message("Mensagem depois do encerramento.")
        assert False, "A sessão encerrada aceitou a mensagem."
    except RuntimeError:
        pass
