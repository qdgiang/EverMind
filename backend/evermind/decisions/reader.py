"""Read helpers for standing decisions and window-shadow semantics."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from evermind.contracts.commands import OpSpec
from evermind.contracts.enums import DecisionStatus
from evermind.decisions.facets import FacetRegistry
from evermind.decisions.models import Decision, EffectiveUnit


class DecisionReader:
    def __init__(self, session: Session, registry: FacetRegistry):
        self.session = session
        self.registry = registry

    def effective_decision_id(self, unit_key: str, *, at: datetime) -> int | None:
        active_windows: list[Decision] = []
        for decision in self.session.scalars(
            select(Decision).where(
                Decision.status == DecisionStatus.EFFECTIVE,
                Decision.effect_window_from <= at,
                Decision.effect_window_until > at,
            )
        ):
            units = self.registry.derive_units(
                [OpSpec.model_validate(op) for op in decision.ops],
                stable_event_id=decision.stable_event_id or str(decision.id),
            )
            if unit_key in {unit.unit_key for unit in units if unit.occupies}:
                active_windows.append(decision)
        if active_windows:
            return max(
                active_windows,
                key=lambda decision: (
                    decision.ts,
                    decision.recorded_at,
                    decision.stable_event_id or "",
                ),
            ).id
        standing = self.session.get(EffectiveUnit, unit_key)
        return standing.decision_id if standing is not None else None
