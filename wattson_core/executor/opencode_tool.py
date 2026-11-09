"""Adaptador restrito para tarefas explícitas no OpenCode."""
from __future__ import annotations

from pathlib import Path

from wattson_core.executor.runner import run_command


class OpenCodeTool:
    """Envia tarefas ao OpenCode sem ativar permissões de escrita ou shell."""

    def __init__(
        self,
        project_root: str | Path,
        executable: str = "opencode",
        timeout_seconds: int = 300,
        model: str = "ollama/qwen3-opencode",
    ):
        self.project_root = Path(project_root).resolve()
        self.executable = executable
        self.timeout_seconds = timeout_seconds
        self.model = model

    def run(self, task: str) -> str:
        task = task.strip()
        if not task:
            raise ValueError("A tarefa para o OpenCode não pode estar vazia.")

        prompt = (
            "Você é uma ferramenta do Wattson Core. "
            "Esta chamada é somente para análise, consulta e planejamento. "
            "Não tente alterar arquivos, executar comandos, instalar pacotes "
            "ou contornar as permissões do projeto. "
            "Examine o contexto disponível e explique limitações com clareza.\n\n"
            f"TAREFA EXPLÍCITA DO USUÁRIO:\n{task}"
        )

        result = run_command(
            [
                self.executable,
                "run",
                "--model",
                self.model,
                prompt,
            ],
            cwd=self.project_root,
            timeout=self.timeout_seconds,
        )

        if result.returncode != 0:
            detail = result.stderr.strip() or result.stdout.strip()
            raise RuntimeError(
                f"OpenCode terminou com código {result.returncode}: {detail}"
            )

        return result.stdout.strip()
