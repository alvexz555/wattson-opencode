from pathlib import Path
import subprocess

from wattson_core.update_manager.git import GitUpdateChecker


def run_git(path: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=path,
        capture_output=True,
        text=True,
        check=True,
    )

    return result.stdout.strip()


def test_git_pull_ff_only_applies_fast_forward(tmp_path):
    remote = tmp_path / "remote.git"
    source = tmp_path / "source"
    client = tmp_path / "client"

    subprocess.run(
        ["git", "init", "--bare", str(remote)],
        check=True,
        capture_output=True,
        text=True,
    )

    subprocess.run(
        ["git", "clone", str(remote), str(source)],
        check=True,
        capture_output=True,
        text=True,
    )

    run_git(source, "config", "user.name", "Test")
    run_git(source, "config", "user.email", "test@example.com")

    (source / "version.txt").write_text("v1")
    run_git(source, "add", "version.txt")
    run_git(source, "commit", "-m", "initial")
    run_git(source, "push", "-u", "origin", "master")

    subprocess.run(
        ["git", "clone", str(remote), str(client)],
        check=True,
        capture_output=True,
        text=True,
    )

    run_git(source, "checkout", "-b", "wattson-core")
    run_git(source, "push", "-u", "origin", "wattson-core")

    run_git(client, "fetch")
    run_git(client, "checkout", "wattson-core")

    (source / "version.txt").write_text("v2")
    run_git(source, "add", "version.txt")
    run_git(source, "commit", "-m", "update")
    run_git(source, "push")

    checker = GitUpdateChecker(str(client))

    checker.fetch()
    assert checker.update_available() is True

    checker.pull_ff_only()

    assert (client / "version.txt").read_text() == "v2"
    assert checker.update_available() is False
def test_git_pull_ff_only_rejects_divergence_and_preserves_local_state(tmp_path):
    remote = tmp_path / "remote.git"
    source = tmp_path / "source"
    client = tmp_path / "client"

    subprocess.run(
        ["git", "init", "--bare", str(remote)],
        check=True,
        capture_output=True,
        text=True,
    )

    subprocess.run(
        ["git", "clone", str(remote), str(source)],
        check=True,
        capture_output=True,
        text=True,
    )

    run_git(source, "config", "user.name", "Test")
    run_git(source, "config", "user.email", "test@example.com")

    (source / "version.txt").write_text("v1")
    run_git(source, "add", "version.txt")
    run_git(source, "commit", "-m", "initial")

    run_git(source, "branch", "-M", "wattson-core")
    run_git(source, "push", "-u", "origin", "wattson-core")

    subprocess.run(
        ["git", "clone", "-b", "wattson-core", str(remote), str(client)],
        check=True,
        capture_output=True,
        text=True,
    )

    # Avanço remoto
    (source / "version.txt").write_text("remote")
    run_git(source, "add", "version.txt")
    run_git(source, "commit", "-m", "remote update")
    run_git(source, "push")

    # Avanço local independente
    run_git(client, "config", "user.name", "Test")
    run_git(client, "config", "user.email", "test@example.com")

    (client / "version.txt").write_text("local")
    run_git(client, "add", "version.txt")
    run_git(client, "commit", "-m", "local update")

    local_commit_before = run_git(client, "rev-parse", "HEAD")

    checker = GitUpdateChecker(str(client))
    checker.fetch()

    assert checker.update_available() is True

    try:
        checker.pull_ff_only()
    except RuntimeError:
        pass
    else:
        raise AssertionError(
            "pull_ff_only deveria rejeitar histórico divergente"
        )

    local_commit_after = run_git(client, "rev-parse", "HEAD")

    assert local_commit_after == local_commit_before
    assert (client / "version.txt").read_text() == "local"
def test_git_pull_ff_only_reaches_target_commit(tmp_path):
    remote = tmp_path / "remote.git"
    source = tmp_path / "source"
    client = tmp_path / "client"

    subprocess.run(
        ["git", "init", "--bare", str(remote)],
        check=True,
        capture_output=True,
        text=True,
    )

    subprocess.run(
        ["git", "clone", str(remote), str(source)],
        check=True,
        capture_output=True,
        text=True,
    )

    run_git(source, "config", "user.name", "Test")
    run_git(source, "config", "user.email", "test@example.com")

    (source / "version.txt").write_text("v1")
    run_git(source, "add", "version.txt")
    run_git(source, "commit", "-m", "initial")
    run_git(source, "branch", "-M", "wattson-core")
    run_git(source, "push", "-u", "origin", "wattson-core")

    subprocess.run(
        ["git", "clone", "-b", "wattson-core", str(remote), str(client)],
        check=True,
        capture_output=True,
        text=True,
    )

    (source / "version.txt").write_text("v2")
    run_git(source, "add", "version.txt")
    run_git(source, "commit", "-m", "update")
    run_git(source, "push")

    checker = GitUpdateChecker(str(client))

    checker.fetch()

    current_before = checker.current_commit()
    target_before = checker.target_commit()

    assert current_before != target_before
    assert checker.update_available() is True

    checker.pull_ff_only()

    current_after = checker.current_commit()
    target_after = checker.target_commit()

    assert current_after == target_before
    assert current_after == target_after
    assert checker.update_available() is False
