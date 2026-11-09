"""Execução externa controlada pelo Wattson."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


class CommandResult:
    def __init__(self, returncode: int, stdout: str, stderr: str):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def run_command(
    command: list[str],
    cwd: str | Path | None = None,
    timeout: int | None = None,
) -> CommandResult:
    try:
        process = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode(errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode(errors="replace")
        return CommandResult(
            returncode=124,
            stdout=stdout,
            stderr=(stderr + f"\\nTempo limite excedido ({timeout}s).").strip(),
        )

    return CommandResult(
        returncode=process.returncode,
        stdout=process.stdout,
        stderr=process.stderr,
    )


def run_adr0(root: str | Path = ".") -> CommandResult:
    return run_command(
        [
            sys.executable,
            "-m",
            "wattson_core.adr0",
            "--format",
            "json",
        ],
        cwd=root,
    )
