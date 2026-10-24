import uuid

from .context import ConversationContext


class Session:
    def __init__(self):
        self.id = str(uuid.uuid4())
        self.context = ConversationContext()
        self.context.session = self
        self.active = True

    def _ensure_active(self) -> None:
        if not self.active:
            raise RuntimeError("Sessão encerrada.")

    def add_message(self, message: str) -> None:
        self._ensure_active()
        self.context.add(message, role="user")

    def clear_context(self) -> None:
        self._ensure_active()
        self.context.clear()

    def close(self) -> None:
        self.active = False
