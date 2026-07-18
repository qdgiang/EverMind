"""Birth-side event ordering context for ING-7 without command-contract changes."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Mapping


@dataclass(frozen=True)
class HandleContext:
    event_ts: datetime
    recorded_at: datetime
    stable_event_id: str
    citation_authors: Mapping[int, int] = field(default_factory=dict)
    delegated_by_user_id: int | None = None
    explicit_supersedes_decision_id: int | None = None

    @classmethod
    def now(cls, stable_event_id: str) -> HandleContext:
        now = datetime.now(UTC).replace(tzinfo=None)
        return cls(event_ts=now, recorded_at=now, stable_event_id=stable_event_id)


def ordering_key(context: HandleContext) -> tuple[datetime, datetime, str]:
    return (context.event_ts, context.recorded_at, context.stable_event_id)
