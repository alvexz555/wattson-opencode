from wattson_core.diagnostics.formatter import DiagnosticFormatter
from wattson_core.update_manager.post_update import PostUpdateValidator
from wattson_core.update_manager.health import PostUpdateHealthChecker
from wattson_core.update_manager.report import UpdateReport


class Orchestrator:
    def __init__(
        self,
        conversation,
        diagnostic_tool=None,
        search_tool=None,
        git_update_checker=None,
        post_update_health_checker=None,
    ):
        self.conversation = conversation
        self.diagnostic_tool = diagnostic_tool
        self.search_tool = search_tool
        self.git_update_checker = git_update_checker
        self.diagnostic_formatter = DiagnosticFormatter()
        self.post_update_validator = PostUpdateValidator()
        self.post_update_health_checker = post_update_health_checker or PostUpdateHealthChecker()

        # Atualização detectada, mas ainda não autorizada.
        self.pending_update = None
        self.last_update_report = None

    def handle(self, message: str) -> str:
        if self._is_update_confirmation(message):
            return self.confirm_update()

        if self._is_update_check_request(message):
            return self.check_for_update()

        if self._is_diagnostic_request(message):
            diagnostic = self.run_diagnostic()
            return self.diagnostic_formatter.format(diagnostic)

        if self._is_search_request(message):
            return self.run_search(message)

        return self.conversation.respond(message)

    def _is_update_confirmation(self, message: str) -> bool:
        confirmations = {
            "sim",
            "s",
            "pode",
            "pode atualizar",
            "atualiza",
            "atualizar",
        }

        return message.strip().lower() in confirmations

    def _is_update_check_request(self, message: str) -> bool:
        keywords = (
            "verificar atualização",
            "verifica atualização",
            "verificar atualizações",
            "verifica atualizações",
            "tem atualização",
            "tem atualizações",
        )

        message_lower = message.strip().lower()

        return any(
            keyword in message_lower
            for keyword in keywords
        )

    def check_for_update(self) -> str:
        if self.git_update_checker is None:
            raise RuntimeError(
                "Ferramenta de atualização não configurada."
            )

        self.git_update_checker.fetch()

        update_info = self.git_update_checker.get_update_info()

        if not update_info.update_available:
            self.pending_update = None
            return "Nenhuma atualização disponível."

        self.pending_update = update_info

        return (
            "Encontrei uma atualização disponível. "
            "Quer atualizar?"
        )

    def confirm_update(self) -> str:
        if self.git_update_checker is None:
            raise RuntimeError("Ferramenta de atualização não configurada.")

        if self.pending_update is None:
            return "Não há atualização aguardando autorização."

        target_commit = self.pending_update.target_commit
        current_commit = self.git_update_checker.current_commit()

        try:
            self.git_update_checker.pull_ff_only()

            current_commit = self.git_update_checker.current_commit()

            health = self.post_update_health_checker.run_all()

            validation = self.post_update_validator.validate(
                target_commit=target_commit,
                current_commit=current_commit,
                tests_passed=health.success,
            )

            if not validation.success:
                self.last_update_report = UpdateReport.create(
                    initiator="orchestrator",
                    current_commit=current_commit,
                    target_commit=target_commit,
                    pytest_passed=health.pytest_passed,
                    imports_passed=health.imports_passed,
                    startup_passed=health.startup_passed,
                    adr0_passed=health.adr0_passed,
                    applied=True,
                    rollback=False,
                    error="Falha na validação pós-update.",
                    final_state="validation_failed",
                )
                return "Atualização falhou na validação pós-update."

        except RuntimeError as exc:
            self.last_update_report = UpdateReport.create(
                initiator="orchestrator",
                current_commit=current_commit,
                target_commit=target_commit,
                pytest_passed=False,
                imports_passed=False,
                startup_passed=False,
                adr0_passed=False,
                applied=False,
                rollback=False,
                error=str(exc),
                final_state="previous_version_active",
            )
            return f"Falha ao aplicar atualização: {exc}"

        self.pending_update = None

        self.last_update_report = UpdateReport.create(
            initiator="orchestrator",
            current_commit=current_commit,
            target_commit=target_commit,
            pytest_passed=health.pytest_passed,
            imports_passed=health.imports_passed,
            startup_passed=health.startup_passed,
            adr0_passed=health.adr0_passed,
            applied=True,
            rollback=False,
            error=None,
            final_state="active",
        )

        return "Atualização aplicada e validada com sucesso."

    def _is_diagnostic_request(self, message: str) -> bool:
        keywords = (
            "diagnóstico",
            "diagnostico",
            "erros",
            "erro",
            "problemas",
        )

        message_lower = message.lower()

        return any(
            keyword in message_lower
            for keyword in keywords
        )

    def _is_search_request(self, message: str) -> bool:
        keywords = (
            "pesquise",
            "pesquisa",
            "procure",
            "busque",
        )

        message_lower = message.strip().lower()

        return any(
            message_lower.startswith(keyword)
            for keyword in keywords
        )

    def run_search(self, query: str):
        if self.search_tool is None:
            raise RuntimeError(
                "Ferramenta de pesquisa não configurada."
            )

        results = self.search_tool.search(query)

        research_prompt = self._build_search_prompt(
            query,
            results,
        )

        return self.conversation.respond(research_prompt)

    def _build_search_prompt(
        self,
        query: str,
        results: list,
    ) -> str:
        results = results[:5]

        lines = [
            f"Pergunta do usuário: {query}",
            "",
            "Resultados encontrados na pesquisa:",
        ]

        for index, result in enumerate(results, start=1):
            title = result.get("title", "")
            url = result.get("url", "")
            content = result.get("content", "")

            lines.extend(
                [
                    "",
                    f"Resultado {index}:",
                    f"Título: {title}",
                    f"URL: {url}",
                    f"Conteúdo: {content}",
                ]
            )

        return "\n".join(lines)

    def run_diagnostic(self):
        if self.diagnostic_tool is None:
            raise RuntimeError(
                "Ferramenta de diagnóstico não configurada."
            )

        return self.diagnostic_tool.run()
