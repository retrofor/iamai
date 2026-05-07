"""Runtime audit logging and in-memory counters for iamai."""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from loguru import logger


@dataclass(frozen=True, slots=True)
class MetricSeries:
    """One metric counter series with labels and value."""

    name: str
    labels: tuple[tuple[str, str], ...]
    value: int

    def formatted_name(self) -> str:
        """Return the metric name with labels rendered in Prometheus style."""
        if not self.labels:
            return self.name
        label_text = ",".join(f"{key}={value}" for key, value in self.labels)
        return f"{self.name}{{{label_text}}}"

    def to_dict(self) -> dict[str, Any]:
        """Return this metric series as a JSON-compatible dictionary."""
        return {
            "name": self.name,
            "labels": dict(self.labels),
            "value": self.value,
        }


class RuntimeMetrics:
    """Small in-memory counter store for health checks and operator inspection."""

    def __init__(self) -> None:
        self._counters: dict[tuple[str, tuple[tuple[str, str], ...]], int] = defaultdict(int)

    def increment(self, name: str, value: int = 1, **labels: Any) -> None:
        """Increment a labeled counter by ``value``."""
        normalized_name = str(name).strip()
        if not normalized_name:
            raise ValueError("metric name cannot be empty")
        label_items = tuple(sorted((str(key), str(item)) for key, item in labels.items()))
        self._counters[(normalized_name, label_items)] += int(value)

    def snapshot(self) -> dict[str, int]:
        """Return counters keyed by their formatted metric names."""
        return {
            MetricSeries(name=name, labels=labels, value=value).formatted_name(): value
            for (name, labels), value in sorted(self._counters.items())
        }

    def series(self) -> list[MetricSeries]:
        """Return all metric series sorted for deterministic output."""
        return [
            MetricSeries(name=name, labels=labels, value=value)
            for (name, labels), value in sorted(self._counters.items())
        ]


class AuditLogger:
    """Structured audit logger that emits one JSON object per runtime event."""

    def __init__(self, logger_name: str = "iamai.audit") -> None:
        self.logger_name = logger_name
        self._logger = logger.bind(name=logger_name, audit=True)

    def emit(
        self,
        action: str,
        *,
        outcome: str = "ok",
        level: int | str = "INFO",
        **fields: Any,
    ) -> None:
        """Emit one structured audit record."""
        payload = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "action": str(action),
            "outcome": str(outcome),
        }
        for key, value in fields.items():
            if value is None:
                continue
            payload[str(key)] = value
        self._logger.log(level, json.dumps(payload, ensure_ascii=False, sort_keys=True))
