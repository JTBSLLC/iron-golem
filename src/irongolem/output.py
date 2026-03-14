from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from irongolem import __version__


@dataclass
class Envelope:
    command: str
    status: str
    phase: str
    duration_ms: int = 0
    data: dict[str, Any] = field(default_factory=dict)
    errors: list[dict[str, Any]] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "version": __version__,
            "command": self.command,
            "status": self.status,
            "phase": self.phase,
            "duration_ms": self.duration_ms,
            "data": self.data,
            "errors": self.errors,
        }
        payload.update(self.extra)
        return payload


def emit_json(payload: dict[str, Any], pretty: bool = False) -> None:
    kwargs: dict[str, Any] = {"sort_keys": True}
    if pretty:
        kwargs["indent"] = 2
    print(json.dumps(payload, **kwargs))
