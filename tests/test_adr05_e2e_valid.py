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
def test_adr05_e2e_valid_update(tmp_path):
    source = Path.cwd()

    snapshot = tmp_path / "snapshot"
    bare = tmp_path / "remote.git"
    publisher = tmp_path / "publisher"
    client = tmp_path / "client"

    # 1. Cria um snapshot do ESTADO ATUAL do projeto.
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

    # 2. Transforma o snapshot em um repositório Git temporário.
    git(snapshot, "init")
    git(snapshot, "config", "user.name", "ADR05-E2E")
    git(snapshot, "config", "user.email", "adr05-e2e@example.invalid")
    git(snapshot, "add", ".")
    git(snapshot, "commit", "-m", "test: ADR 0.5 E2E base")

    # 3. Cria o remoto temporário.
    git(tmp_path, "clone", "--bare", str(snapshot), str(bare))

    # 4. Cria o clone que representa o VAIO.
    git(tmp_path, "clone", str(bare), str(client))

    initial_commit = git(client, "rev-parse", "HEAD")

    # 5. Cria o publicador que representa o Pi.
    git(tmp_path, "clone", str(bare), str(publisher))

    marker = publisher / "e2e_marker.txt"
    marker.write_text(
        "ADR 0.5 E2E VALID UPDATE\n",
        encoding="utf-8",
    )

    git(publisher, "add", "e2e_marker.txt")
    git(
        publisher,
        "commit",
        "-m",
        "test: ADR 0.5 valid E2E update",
    )

    target_commit = git(publisher, "rev-parse", "HEAD")

    # 6. Publicação do Pi no remoto.
    git(publisher, "push", "origin", "HEAD")

    assert initial_commit != target_commit

    # 7. Conversation mínima para o Orchestrator.
    class FakeConversation:
        def respond(self, message: str) -> str:
            return "resposta"

    # 8. Orchestrator usando Git e Health Check REAIS
    #    contra o clone temporário.
    git_checker = GitUpdateChecker(
        repository_path=str(client)
    )

    health_checker = PostUpdateHealthChecker(
        repository_path=str(client)
    )

    orchestrator = Orchestrator(
        FakeConversation(),
        git_update_checker=git_checker,
        post_update_health_checker=health_checker,
    )

    # 9. Detecção real da atualização.
    detection = orchestrator.handle(
        "verificar atualização"
    )

    assert "atualização" in detection.lower()
    assert orchestrator.pending_update is not None
    assert (
        orchestrator.pending_update.target_commit
        == target_commit
    )

    # 10. Autorização + aplicação real.
    result = orchestrator.handle("sim")

    # 11. Confirmações finais.
    current_commit = git_checker.current_commit()

    assert result == (
        "Atualização aplicada e validada com sucesso."
    )

    assert current_commit == target_commit

    assert (client / "e2e_marker.txt").read_text(
        encoding="utf-8"
    ) == "ADR 0.5 E2E VALID UPDATE\n"

    # 12. Relatório final.
    report = orchestrator.last_update_report

    assert report is not None
    assert report.current_commit == target_commit
    assert report.target_commit == target_commit

    assert report.applied is True
    assert report.rollback is False
    assert report.error is None
    assert report.final_state == "active"

    assert report.pytest_passed is True
    assert report.imports_passed is True
    assert report.startup_passed is True
    assert report.adr0_passed is True
