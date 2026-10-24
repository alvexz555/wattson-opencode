from wattson_core.ai.conversation import ConversationAI
from wattson_core.ai.engine import AIEngine
from wattson_core.ai.context import ConversationContext


class FakeProvider:
    def generate(self, prompt: str) -> str:
        return f"resposta: {prompt}"


def test_conversation_ai_generates_response():
    engine = AIEngine(FakeProvider())
    context = ConversationContext()
    conversation = ConversationAI(engine, context)

    result = conversation.respond("Olá, Wattson")

    assert result.startswith("resposta: Você é Wattson")
    assert "Usuário: Olá, Wattson" in result


def test_conversation_ai_uses_ai_engine():
    class SpyEngine:
        def __init__(self):
            self.received_message = None

        def generate(self, prompt: str) -> str:
            self.received_message = prompt
            return "resposta do engine"

    engine = SpyEngine()
    context = ConversationContext()
    conversation = ConversationAI(engine, context)

    result = conversation.respond("Teste de integração")

    assert "Teste de integração" in engine.received_message
    assert "Instruções:" in engine.received_message
    assert "não inventar informações" in engine.received_message
    assert result == "resposta do engine"
