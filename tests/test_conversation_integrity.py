import pytest

from wattson_core.ai.context import ConversationContext
from wattson_core.ai.conversation import ConversationAI
from wattson_core.ai.session import Session


class FakeEngine:
    def generate(self, prompt: str) -> str:
        return "resposta de teste"


class BrokenEngine:
    def generate(self, prompt: str) -> str:
        raise RuntimeError("Falha simulada do provedor")


class InvalidResponseEngine:
    def generate(self, prompt: str):
        return None


def test_context_tracks_explicit_message_roles():
    context = ConversationContext()

    context.add("Olá", role="user")
    context.add("Olá! Como posso ajudar?", role="assistant")
    context.add("Outra pergunta", role="user")

    assert context.messages == [
        "Olá",
        "Olá! Como posso ajudar?",
        "Outra pergunta",
    ]
    assert context.roles == ["user", "assistant", "user"]
    assert context.get_entries() == [
        ("user", "Olá"),
        ("assistant", "Olá! Como posso ajudar?"),
        ("user", "Outra pergunta"),
    ]


def test_context_clear_removes_messages_and_roles():
    context = ConversationContext()
    context.add("Pergunta", role="user")
    context.add("Resposta", role="assistant")

    context.clear()

    assert context.messages == []
    assert context.roles == []
    assert context.get_entries() == []


def test_context_rejects_invalid_role():
    context = ConversationContext()

    with pytest.raises(ValueError):
        context.add("Mensagem", role="invalid")


def test_context_detects_message_role_mismatch():
    context = ConversationContext()
    context.add("Mensagem")
    context.messages.append("Alteração externa")

    with pytest.raises(RuntimeError, match="Histórico inconsistente"):
        context.get_entries()


def test_provider_failure_preserves_user_message_without_fake_reply():
    context = ConversationContext()
    conversation = ConversationAI(BrokenEngine(), context)

    with pytest.raises(RuntimeError, match="Falha simulada"):
        conversation.respond("Pergunta que falhou")

    assert context.messages == ["Pergunta que falhou"]
    assert context.roles == ["user"]
    assert context.get_entries() == [
        ("user", "Pergunta que falhou"),
    ]


def test_non_string_provider_response_is_rejected():
    context = ConversationContext()
    conversation = ConversationAI(InvalidResponseEngine(), context)

    with pytest.raises(TypeError, match="resposta do modelo"):
        conversation.respond("Pergunta")

    assert context.messages == ["Pergunta"]
    assert context.roles == ["user"]


def test_closed_session_rejects_conversation_response():
    session = Session()
    conversation = ConversationAI(FakeEngine(), session.context)
    session.close()

    with pytest.raises(RuntimeError, match="Sessão encerrada"):
        conversation.respond("Não deve ser processada")

    assert session.context.messages == []
    assert session.context.roles == []


def test_closed_session_rejects_direct_context_add_and_clear():
    session = Session()
    session.context.add("Mensagem existente")
    session.close()

    with pytest.raises(RuntimeError, match="Sessão encerrada"):
        session.context.add("Mensagem proibida")

    with pytest.raises(RuntimeError, match="Sessão encerrada"):
        session.clear_context()

    assert session.context.messages == ["Mensagem existente"]
    assert session.context.roles == ["user"]


def test_failed_response_can_be_followed_by_successful_response():
    context = ConversationContext()
    conversation = ConversationAI(BrokenEngine(), context)

    with pytest.raises(RuntimeError):
        conversation.respond("Primeira pergunta")

    conversation.engine = FakeEngine()
    result = conversation.respond("Segunda pergunta")

    assert result == "resposta de teste"
    assert context.get_entries() == [
        ("user", "Primeira pergunta"),
        ("user", "Segunda pergunta"),
        ("assistant", "resposta de teste"),
    ]
