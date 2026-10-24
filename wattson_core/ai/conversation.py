from .identity import WattsonIdentity
from .instructions import WattsonInstructions


class ConversationAI:
    def __init__(self, engine, context):
        self.engine = engine
        self.context = context
        self.identity = WattsonIdentity()
        self.instructions = WattsonInstructions()

    def _build_prompt(self) -> str:
        rules = "\n".join(
            f"- {rule}" for rule in self.instructions.rules
        )

        role_labels = {
            "user": "Usuário",
            "assistant": "Wattson",
            "system": "Sistema",
            "tool": "Ferramenta",
        }

        history = []
        for role, message in self.context.get_entries():
            label = role_labels.get(role, role)
            history.append(f"{label}: {message}")

        return (
            f"Você é {self.identity.name}, uma IA pessoal cujo propósito é "
            f"{self.identity.purpose}.\n"
            "Responda em português brasileiro, de forma natural, direta e útil. "
            "Entenda a pergunta antes de responder. Use o contexto da conversa, "
            "evite repetir informações sem necessidade e não invente fatos. "
            "Quando não souber algo, diga isso claramente. "
            "Em pedidos práticos, dê passos concretos e proporcionais ao pedido.\n"
            f"Instruções:\n{rules}\n\n"
            "Histórico da conversa:\n"
            + "\n".join(history)
            + "\nWattson:"
        )

    def respond(self, message: str) -> str:
        self.context._ensure_active()

        if not isinstance(message, str):
            raise TypeError("Mensagem deve ser uma string.")

        self.context.add(message, role="user")
        prompt = self._build_prompt()

        # Se o provedor falhar, preservamos a mensagem do usuário.
        # A exceção continua sendo propagada para quem chamou.
        response = self.engine.generate(prompt)

        if not isinstance(response, str):
            raise TypeError("A resposta do modelo deve ser uma string.")

        self.context.add(response, role="assistant")
        return response
