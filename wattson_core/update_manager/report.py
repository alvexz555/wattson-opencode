"""Relatório estruturado de uma tentativa de atualização."""

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import platform
from typing import Optional


@dataclass(frozen=True)
class UpdateReport:
    timestamp: str
    device: str
    initiator: str
    current_commit: str
    target_commit: str

    pytest_passed: bool
    imports_passed: bool
    startup_passed: bool
    adr0_passed: bool

    applied: bool
    rollback: bool
    error: Optional[str]
    final_state: str

    @classmethod
    def create(
        cls,
        *,
        initiator: str,
        current_commit: str,
        target_commit: str,
        pytest_passed: bool,
        imports_passed: bool,
        startup_passed: bool,
        adr0_passed: bool,
        applied: bool,
        rollback: bool,
        error: Optional[str],
        final_state: str,
    ) -> "UpdateReport":
        return cls(
            timestamp=datetime.now(timezone.utc).isoformat(),
            device=platform.node(),
            initiator=initiator,
            current_commit=current_commit,
            target_commit=target_commit,
            pytest_passed=pytest_passed,
            imports_passed=imports_passed,
            startup_passed=startup_passed,
            adr0_passed=adr0_passed,
            applied=applied,
            rollback=rollback,
            error=error,
            final_state=final_state,
        )

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(),
            ensure_ascii=False,
            indent=2,
        )
