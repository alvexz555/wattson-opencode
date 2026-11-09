from wattson_core.ai.context import ConversationContext
import pytest
pytestmark = pytest.mark.integration
from wattson_core.ai.conversation import ConversationAI
from wattson_core.ai.engine import AIEngine
from wattson_core.ai.providers.ollama import WattsonProvider
from wattson_core.core.orchestrator import Orchestrator


def test_orchestrator_reaches_real_dolphin():
    """Integração real com o Ollama: depende de infraestrutura local e do tempo de geração do modelo.

    Marcada como 'integration' para a suíte padrão (pytest.ini: -m "not integration") ficar determinística.
    """
    provider = WattsonProvider()
    engine = AIEngine(provider)
    context = ConversationContext()
    conversation = ConversationAI(engine, context)
    orchestrator = Orchestrator(conversation)

    response = orchestrator.handle(
        "Olá, Wattson. Responda apenas confirmando que você recebeu a mensagem."
    )

    assert isinstance(response, str)
    assert response.strip()

    assert context.messages[0] == (
        "Olá, Wattson. Responda apenas confirmando que você recebeu a mensagem."
    )

    assert context.messages[-1] == response
