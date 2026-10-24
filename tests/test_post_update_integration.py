from types import SimpleNamespace

from wattson_core.core.orchestrator import Orchestrator


class FakeGitUpdateChecker:
    def __init__(self):
        self.pulled = False
        self.current = "abc123"

    def pull_ff_only(self):
        self.pulled = True

    def current_commit(self):
        return self.current


class FakePostUpdateHealthChecker:
    def __init__(self, success=True):
        self.success = success
        self.calls = 0

    def run_all(self):
        self.calls += 1
        return SimpleNamespace(
            pytest_passed=True,
            imports_passed=True,
            startup_passed=True,
            adr0_passed=True,
            success=self.success,
        )


class FakePostUpdateValidator:
    def __init__(self, success=True):
        self.success = success
        self.calls = []

    def validate(self, target_commit, current_commit, tests_passed):
        self.calls.append(
            (target_commit, current_commit, tests_passed)
        )
        return SimpleNamespace(
            success=(
                self.success
                and current_commit == target_commit
                and tests_passed
            )
        )


def make_orchestrator(
    *,
    target_commit="abc123",
    current_commit="abc123",
    validator_success=True,
):
    git = FakeGitUpdateChecker()
    git.current = current_commit

    validator = FakePostUpdateValidator(
        success=validator_success
    )

    health_checker = FakePostUpdateHealthChecker(
        success=True
    )

    orchestrator = Orchestrator(
        conversation=None,
        git_update_checker=git,
        post_update_health_checker=health_checker,
    )

    orchestrator.post_update_validator = validator
    orchestrator.pending_update = SimpleNamespace(
        target_commit=target_commit
    )

    return orchestrator, git, validator


def test_valid_update_passes_post_update_validation():
    orchestrator, git, validator = make_orchestrator()

    result = orchestrator.confirm_update()

    assert git.pulled is True
    assert validator.calls == [
        ("abc123", "abc123", True)
    ]
    assert result == "Atualização aplicada e validada com sucesso."
    assert orchestrator.pending_update is None


def test_wrong_sha_fails_post_update_validation():
    orchestrator, git, validator = make_orchestrator(
        target_commit="expected",
        current_commit="different",
    )

    result = orchestrator.confirm_update()

    assert git.pulled is True
    assert validator.calls == [
        ("expected", "different", True)
    ]
    assert result == "Atualização falhou na validação pós-update."
    assert orchestrator.pending_update is not None


def test_failed_update_tests_are_not_reported_as_success():
    orchestrator, git, validator = make_orchestrator(
        validator_success=False,
    )

    result = orchestrator.confirm_update()

    assert git.pulled is True
    assert validator.calls == [
        ("abc123", "abc123", True)
    ]
    assert result == "Atualização falhou na validação pós-update."
    assert orchestrator.pending_update is not None


def test_confirmation_without_pending_update_is_blocked():
    orchestrator, git, validator = make_orchestrator()
    orchestrator.pending_update = None

    result = orchestrator.confirm_update()

    assert git.pulled is False
    assert validator.calls == []
    assert result == "Não há atualização aguardando autorização."
