"""Domain event catalog — appended by `decisions` (A) in the same transaction as
the write; consumed only by projections (`tasks`/`signals`/`surfacing`/`knowledge`,
all B except knowledge). Event shape changes are contract PRs, never silent
(work-split.md §A<->B interfaces, item 3).

Projections track their own read position in a `projection_offsets` row keyed by
consumer name — see `evermind.decisions.models.ProjectionOffset`.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel


class DomainEvent(BaseModel):
    seq: int
    ts: datetime
    kind: str
    aggregate: str  # e.g. "decision", "task_update", "signal", "reaction_act"
    aggregate_id: int
    payload: dict[str, Any]
    caused_by_command: str | None = None  # client_command_id


EventKind = Literal[
    # decisions lifecycle (A appends; B's tasks/surfacing fold)
    "decision_proposed",
    "decision_effective",  # payload.windowed=True for effect-window decisions (G42)
    "decision_superseded",
    "decision_rejected",  # payload.rejected_reason: veto|overruled|withdrawn|dismissed
    "decision_born_superseded",  # ING-7/G31: late older same-unit decision enters history
    "decision_resurrected",  # DEC-6/G17: rejection restored the superseded predecessor
    "proposal_merged",  # DEC-7/G49: dedup-merge into an existing pending (payload.into)
    "proposal_withdrawn",  # settled #17b: proposer's own newer value withdrew the older
    "challenge_filed",  # DEC-6/G18: insufficient-rank reject files a challenge
    "triage_raised",  # UNLINKED / impossible-chronology triage card [EVM-012]
    # task-update lanes (gateway-routed, TSK-2; B's fold applies)
    "task_update_recorded",  # payload.lane: pic_auto | authority
    "task_update_pending_confirm",  # non-PIC, non-authority => PIC confirm card (G9)
    # signals (B's ledger folds these)
    "signal_recorded",
    "signal_promoted",
    "signal_expired",
    # acts & evidence
    "corroboration_appended",  # G66 same-value guard / corroboration lane
    "reaction_act_registered",  # DEC-5 (P3)
]
