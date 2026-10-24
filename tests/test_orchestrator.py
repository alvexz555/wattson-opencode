from wattson_core.core.orchestrator import Orchestrator


def test_orchestrator_delegates_message_to_conversation():
    class FakeConversation:
        def __init__(self):
            self.received_message = None

        def respond(self, message: str) -> str:
            self.received_message = message
            return "resposta da conversa"

    conversation = FakeConversation()
    orchestrator = Orchestrator(conversation)

    result = orchestrator.handle("Olá, Wattson")

    assert conversation.received_message == "Olá, Wattson"
    assert result == "resposta da conversa"
def test_orchestrator_reports_available_update():
    class FakeConversation:
        def respond(self, message: str) -> str:
            return "resposta da conversa"

    class FakeGitUpdateChecker:
        def fetch(self):
            pass

        def get_update_info(self):
            class Info:
                update_available = True
                current_commit = "abc123"
                target_commit = "def456"

            return Info()

    orchestrator = Orchestrator(
        FakeConversation(),
        git_update_checker=FakeGitUpdateChecker(),
    )

    result = orchestrator.handle("verificar atualização")

    assert "atualização" in result.lower()
    assert "quer atualizar" in result.lower()
def test_orchestrator_requires_pending_update_before_confirmation():
    class FakeConversation:
        def respond(self, message: str) -> str:
            return "resposta"

    class FakeGitUpdateChecker:
        def __init__(self):
            self.pull_called = False

        def pull_ff_only(self):
            self.pull_called = True

        def current_commit(self):
            return "def456"

    checker = FakeGitUpdateChecker()

    orchestrator = Orchestrator(
        FakeConversation(),
        git_update_checker=checker,
    )

    result = orchestrator.handle("sim")

    assert "não há atualização" in result.lower()
    assert checker.pull_called is False
def test_orchestrator_confirms_and_applies_pending_update():
    class FakeConversation:
        def respond(self, message: str) -> str:
            return "resposta"

    class FakeGitUpdateChecker:
        def __init__(self):
            self.pull_called = False

        def fetch(self):
            pass

        def get_update_info(self):
            class Info:
                update_available = True
                current_commit = "abc123"
                target_commit = "def456"

            return Info()

        def pull_ff_only(self):
            self.pull_called = True

        def current_commit(self):
            return "def456"

    checker = FakeGitUpdateChecker()

    class FakeHealthChecker:
        def run_all(self):
            class Result:
                pytest_passed = True
                imports_passed = True
                startup_passed = True
                adr0_passed = True
                success = True

            return Result()

    health_checker = FakeHealthChecker()

    orchestrator = Orchestrator(
        FakeConversation(),
        git_update_checker=checker,
        post_update_health_checker=health_checker,
    )

    check_result = orchestrator.handle(
        "verificar atualização"
    )

    assert "quer atualizar" in check_result.lower()
    assert orchestrator.pending_update is not None

    result = orchestrator.handle("sim")

    assert "aplicada" in result.lower()
    assert checker.pull_called is True
    assert orchestrator.pending_update is None
def test_orchestrator_preserves_pending_update_when_update_fails():
    class FakeConversation:
        def respond(self, message: str) -> str:
            return "resposta"

    class FakeGitUpdateChecker:
        def fetch(self):
            pass

        def get_update_info(self):
            class Info:
                update_available = True
                current_commit = "abc123"
                target_commit = "def456"

            return Info()

        def current_commit(self):
            return "abc123"

        def pull_ff_only(self):
            raise RuntimeError("Fast-forward impossível")

    checker = FakeGitUpdateChecker()

    orchestrator = Orchestrator(
        FakeConversation(),
        git_update_checker=checker,
    )

    check_result = orchestrator.handle(
        "verificar atualização"
    )

    assert "quer atualizar" in check_result.lower()
    assert orchestrator.pending_update is not None

    result = orchestrator.handle("sim")

    assert "falha" in result.lower()
    assert orchestrator.pending_update is not None


def test_orchestrator_report_records_successful_update():
    class FakeConversation:
        def respond(self, message: str) -> str:
            return "resposta"

    class FakeGitUpdateChecker:
        def fetch(self):
            pass

        def get_update_info(self):
            class Info:
                update_available = True
                current_commit = "abc123"
                target_commit = "def456"

            return Info()

        def pull_ff_only(self):
            pass

        def current_commit(self):
            return "def456"

    class FakeHealthChecker:
        def run_all(self):
            class Result:
                pytest_passed = True
                imports_passed = True
                startup_passed = True
                adr0_passed = True
                success = True

            return Result()

    orchestrator = Orchestrator(
        FakeConversation(),
        git_update_checker=FakeGitUpdateChecker(),
        post_update_health_checker=FakeHealthChecker(),
    )

    orchestrator.handle("verificar atualização")
    result = orchestrator.handle("sim")

    report = orchestrator.last_update_report

    assert result == "Atualização aplicada e validada com sucesso."
    assert report is not None
    assert report.current_commit == "def456"
    assert report.target_commit == "def456"
    assert report.applied is True
    assert report.rollback is False
    assert report.error is None
    assert report.final_state == "active"
    assert report.pytest_passed is True
    assert report.imports_passed is True
    assert report.startup_passed is True
    assert report.adr0_passed is True


def test_orchestrator_report_records_validation_failure():
    class FakeConversation:
        def respond(self, message: str) -> str:
            return "resposta"

    class FakeGitUpdateChecker:
        def fetch(self):
            pass

        def get_update_info(self):
            class Info:
                update_available = True
                current_commit = "abc123"
                target_commit = "def456"

            return Info()

        def pull_ff_only(self):
            pass

        def current_commit(self):
            return "def456"

    class FakeHealthChecker:
        def run_all(self):
            class Result:
                pytest_passed = False
                imports_passed = True
                startup_passed = True
                adr0_passed = True
                success = False

            return Result()

    orchestrator = Orchestrator(
        FakeConversation(),
        git_update_checker=FakeGitUpdateChecker(),
        post_update_health_checker=FakeHealthChecker(),
    )

    orchestrator.handle("verificar atualização")
    result = orchestrator.handle("sim")

    report = orchestrator.last_update_report

    assert result == "Atualização falhou na validação pós-update."
    assert report is not None
    assert report.applied is True
    assert report.rollback is False
    assert report.error == "Falha na validação pós-update."
    assert report.final_state == "validation_failed"
    assert report.pytest_passed is False
    assert orchestrator.pending_update is not None


def test_orchestrator_report_records_update_failure():
    class FakeConversation:
        def respond(self, message: str) -> str:
            return "resposta"

    class FakeGitUpdateChecker:
        def fetch(self):
            pass

        def get_update_info(self):
            class Info:
                update_available = True
                current_commit = "abc123"
                target_commit = "def456"

            return Info()

        def current_commit(self):
            return "abc123"

        def pull_ff_only(self):
            raise RuntimeError("Fast-forward impossível")

    orchestrator = Orchestrator(
        FakeConversation(),
        git_update_checker=FakeGitUpdateChecker(),
    )

    orchestrator.handle("verificar atualização")
    result = orchestrator.handle("sim")

    report = orchestrator.last_update_report

    assert "falha" in result.lower()
    assert report is not None
    assert report.current_commit == "abc123"
    assert report.target_commit == "def456"
    assert report.applied is False
    assert report.rollback is False
    assert report.error == "Fast-forward impossível"
    assert report.final_state == "previous_version_active"
    assert orchestrator.pending_update is not None
