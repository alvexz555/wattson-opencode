import shutil
import subprocess
from pathlib import Path

import pytest

from wattson_core.core.orchestrator import Orchestrator
from wattson_core.update_manager.git import GitUpdateChecker
from wattson_core.update_manager.health import PostUpdateHealthChecker


def git(path, *args):
    result = subprocess.run(
        ["git", *args],
        cwd=path,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, (
        f"Git falhou: git {' '.join(args)}\n"
        f"stdout={result.stdout}\n"
        f"stderr={result.stderr}"
    )

    return result.stdout.strip()


@pytest.mark.integration
def test_adr05_e2e_invalid_update(tmp_path):
    source = Path.cwd()

    snapshot = tmp_path / "snapshot"
    bare = tmp_path / "remote.git"
    publisher = tmp_path / "publisher"
    client = tmp_path / "client"

    # 1. Snapshot do estado atual.
    shutil.copytree(
        source,
        snapshot,
        ignore=shutil.ignore_patterns(
            ".git",
            ".venv",
            "__pycache__",
            ".pytest_cache",
        ),
    )

    # 2. Repositório Git temporário saudável.
    git(snapshot, "init")
    git(snapshot, "config", "user.name", "ADR05-E2E")
    git(snapshot, "config", "user.email", "adr05-e2e@example.invalid")
    git(snapshot, "add", ".")
    git(snapshot, "commit", "-m", "test: ADR 0.5 invalid E2E base")

    # 3. Remote temporário.
    git(tmp_path, "clone", "--bare", str(snapshot), str(bare))

    # 4. Cliente = VAIO.
    git(tmp_path, "clone", str(bare), str(client))
    initial_commit = git(client, "rev-parse", "HEAD")

    # 5. Publisher = Pi.
    git(tmp_path, "clone", str(bare), str(publisher))

    marker = publisher / "e2e_invalid_marker.txt"
    marker.write_text(
        "ADR 0.5 E2E INVALID UPDATE\n",
        encoding="utf-8",
    )

    git(publisher, "add", "e2e_invalid_marker.txt")
    git(
        publisher,
        "commit",
        "-m",
        "test: ADR 0.5 invalid E2E update",
    )

    target_commit = git(publisher, "rev-parse", "HEAD")
    git(publisher, "push", "origin", "HEAD")

    assert initial_commit != target_commit

    class FakeConversation:
        def respond(self, message: str) -> str:
            return "resposta"

    git_checker = GitUpdateChecker(
        repository_path=str(client)
    )

    real_health_checker = PostUpdateHealthChecker(
        repository_path=str(client)
    )

    # Health Check real, mas com pytest sabotado.
    class InvalidHealthChecker:
        def __init__(self):
            self.real = real_health_checker

        def run_all(self):
            result = self.real.run_all()

            class InvalidResult:
                pytest_passed = False
                imports_passed = result.imports_passed
                startup_passed = result.startup_passed
                adr0_passed = result.adr0_passed
                success = False

            return InvalidResult()

    orchestrator = Orchestrator(
        FakeConversation(),
        git_update_checker=git_checker,
        post_update_health_checker=InvalidHealthChecker(),
    )

    # 6. Detecta a atualização.
    detection = orchestrator.handle(
        "verificar atualização"
    )

    assert "atualização" in detection.lower()
    assert orchestrator.pending_update is not None
    assert (
        orchestrator.pending_update.target_commit
        == target_commit
    )

    # 7. Autoriza e aplica.
    result = orchestrator.handle("sim")

    # 8. O Git foi atualizado, mas a validação deve rejeitar.
    current_commit = git_checker.current_commit()

    assert current_commit == target_commit

    assert result == (
        "Atualização falhou na validação pós-update."
    )

    # 9. O pending update permanece disponível,
    #    porque a validação falhou.
    assert orchestrator.pending_update is not None

    # 10. Report registra a falha.
    report = orchestrator.last_update_report

    assert report is not None
    assert report.current_commit == target_commit
    assert report.target_commit == target_commit

    assert report.applied is True
    assert report.rollback is False
    assert report.error == (
        "Falha na validação pós-update."
    )
    assert report.final_state == "validation_failed"

    assert report.pytest_passed is False
    assert report.imports_passed is True
    assert report.startup_passed is True
    assert report.adr0_passed is True
