"""Eventos estruturados, com sanitização e falha isolada."""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Any, Callable

_SENSITIVE_KEY = re.compile(
    r"password|passwd|secret|api[_-]?key|access[_-]?token|"
    r"refresh[_-]?token|authorization|credential|private[_-]?key",
    re.IGNORECASE,
)

_SECRET_TEXT = re.compile(
    r"(?i)\b(password|passwd|secret|api[_-]?key|access[_-]?token|"
    r"refresh[_-]?token|authorization|credential)\b"
    r"(\s*[:=]\s*)[^\s,;]+"
)

_BEARER = re.compile(
    r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+"
)


def _safe_text(value: str) -> str:
    """Remove credenciais comuns de textos antes de registrá-los."""
    value = _BEARER.sub("Bearer [REDACTED]", value)
    return _SECRET_TEXT.sub(r"\1\2[REDACTED]", value)


def _sanitize(value: Any, depth: int = 0, seen: set[int] | None = None) -> Any:
    """Converte valores para uma estrutura segura e serializável."""
    if depth > 8:
        return "[MAX_DEPTH]"

    if value is None or isinstance(value, (bool, int, float)):
        return value

    if isinstance(value, str):
        return _safe_text(value)

    if seen is None:
        seen = set()

    if isinstance(value, dict):
        identity = id(value)
        if identity in seen:
            return "[CIRCULAR]"
        seen.add(identity)
        try:
            result = {}
            for key, item in list(value.items())[:100]:
                try:
                    safe_key = str(key)[:200]
                except Exception:
                    safe_key = "[INVALID_KEY]"

                if _SENSITIVE_KEY.search(safe_key):
                    result[safe_key] = "[REDACTED]"
                else:
                    result[safe_key] = _sanitize(item, depth + 1, seen)
            return result
        finally:
            seen.discard(identity)

    if isinstance(value, (list, tuple)):
        identity = id(value)
        if identity in seen:
            return "[CIRCULAR]"
        seen.add(identity)
        try:
            return [
                _sanitize(item, depth + 1, seen)
                for item in value[:100]
            ]
        finally:
            seen.discard(identity)

    # Não registrar repr() de objetos desconhecidos: pode conter segredos.
    return f"[UNSUPPORTED:{type(value).__name__}]"


def build_event(
    event_type: str,
    component: str,
    level: str = "INFO",
    status: str = "ok",
    message: str = "",
    correlation_id: str | None = None,
    fields: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Cria um evento estruturado sem depender de serviços externos."""
    try:
        safe_fields = _sanitize(fields or {})
        if not isinstance(safe_fields, dict):
            safe_fields = {}

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": _safe_text(str(event_type)[:200]),
            "component": _safe_text(str(component)[:200]),
            "level": _safe_text(str(level).upper()[:20]),
            "status": _safe_text(str(status)[:50]),
            "message": _safe_text(str(message)[:2000]),
            "correlation_id": (
                _safe_text(str(correlation_id)[:200])
                if correlation_id
                else str(uuid.uuid4())
            ),
            "fields": safe_fields,
        }
    except Exception:
        # A construção do evento nunca deve derrubar o fluxo principal.
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "observability.error",
            "component": "observability",
            "level": "WARNING",
            "status": "degraded",
            "message": "Falha ao construir evento; detalhes omitidos.",
            "correlation_id": str(uuid.uuid4()),
            "fields": {},
        }


def emit_event(
    event_type: str,
    component: str,
    level: str = "INFO",
    status: str = "ok",
    message: str = "",
    correlation_id: str | None = None,
    fields: dict[str, Any] | None = None,
    sink: Callable[[dict[str, Any]], Any] | None = None,
) -> dict[str, Any]:
    """Constrói e entrega um evento; falhas do destino são isoladas."""
    event = build_event(
        event_type=event_type,
        component=component,
        level=level,
        status=status,
        message=message,
        correlation_id=correlation_id,
        fields=fields,
    )

    if sink is not None:
        try:
            sink(event)
        except Exception:
            # A instrumentação é secundária: não propaga falhas do destino.
            pass

    return event
