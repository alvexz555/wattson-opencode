class ConversationContext:
    VALID_ROLES = {"user", "assistant", "system", "tool"}

    def __init__(self):
        self.messages: list[str] = []
        self.roles: list[str] = []
        self.session = None

    def _ensure_active(self) -> None:
        if self.session is not None and not self.session.active:
            raise RuntimeError("Sessão encerrada.")

    def _ensure_consistent(self) -> None:
        if len(self.messages) != len(self.roles):
            raise RuntimeError(
                "Histórico inconsistente: quantidade de mensagens "
                "diferente da quantidade de papéis."
            )

    def add(self, message: str, role: str = "user") -> None:
        self._ensure_active()
        self._ensure_consistent()

        if not isinstance(message, str):
            raise TypeError("Mensagem deve ser uma string.")
        if role not in self.VALID_ROLES:
            raise ValueError(f"Papel de mensagem inválido: {role!r}")

        self.messages.append(message)
        self.roles.append(role)

    def get_messages(self) -> list[str]:
        return self.messages

    def get_entries(self) -> list[tuple[str, str]]:
        self._ensure_consistent()
        return list(zip(self.roles, self.messages))

    def remove_last(self) -> None:
        self._ensure_active()
        self._ensure_consistent()

        if self.messages:
            self.messages.pop()
            self.roles.pop()

    def clear(self) -> None:
        self._ensure_active()
        self._ensure_consistent()
        self.messages.clear()
        self.roles.clear()
