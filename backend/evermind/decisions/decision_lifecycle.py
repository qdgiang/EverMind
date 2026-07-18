"""Lifecycle, supersession, and effective-unit persistence for decision writes."""

from __future__ import annotations

from sqlalchemy import delete, select

from evermind.contracts.commands import CitationSpec, OpSpec
from evermind.contracts.enums import CitationKind, DecisionStatus, RejectedReason
from evermind.db.eventlog import DomainEvent
from evermind.decisions.decision_policy import DecisionPolicy
from evermind.decisions.facets import DerivedUnit
from evermind.decisions.models import (
    Decision,
    DecisionCitation,
    EffectiveUnit,
)
from evermind.decisions.ordering import HandleContext
from evermind.decisions.persistence import append_event


class DecisionLifecycle(DecisionPolicy):
    @staticmethod
    def _chronology_state(
        context: HandleContext,
        predecessors: list[Decision],
    ) -> str:
        explicit_id = context.explicit_supersedes_decision_id
        if explicit_id is not None:
            explicit = next(
                (
                    predecessor
                    for predecessor in predecessors
                    if predecessor.id == explicit_id
                ),
                None,
            )
            if explicit is None:
                return "conflict"
            explicit_key = (
                explicit.ts,
                explicit.recorded_at,
                explicit.stable_event_id or "",
            )
            if (
                context.event_ts,
                context.recorded_at,
                context.stable_event_id,
            ) <= explicit_key:
                return "conflict"
        if not predecessors:
            return "current"
        new_key = (context.event_ts, context.recorded_at, context.stable_event_id)
        prior_keys = [
            (
                predecessor.ts,
                predecessor.recorded_at,
                predecessor.stable_event_id or "",
            )
            for predecessor in predecessors
        ]
        older = [new_key < prior_key for prior_key in prior_keys]
        if all(older):
            return "late"
        if any(older):
            return "conflict"
        return "current"

    def _resurrect_predecessors(
        self,
        rejected: Decision,
        *,
        context: HandleContext,
        command_id: str,
    ) -> list[int]:
        effective_event = next(
            (
                event
                for event in self.session.scalars(
                    select(DomainEvent)
                    .where(
                        DomainEvent.kind == "decision_effective",
                        DomainEvent.aggregate == "decision",
                        DomainEvent.aggregate_id == rejected.id,
                    )
                    .order_by(DomainEvent.seq)
                )
                if "displaced_units" in event.payload
            ),
            None,
        )
        displaced_units = (
            list(effective_event.payload.get("displaced_units", []))
            if effective_event is not None
            else []
        )
        restored_by_predecessor: dict[int, list[str]] = {}
        for displacement in displaced_units:
            unit_key = displacement.get("unit_key")
            predecessor_id = displacement.get("decision_id")
            if not isinstance(unit_key, str) or not isinstance(predecessor_id, int):
                continue
            if self.session.get(EffectiveUnit, unit_key) is not None:
                continue
            predecessor = self.session.get(Decision, predecessor_id)
            if predecessor is None or predecessor.status is DecisionStatus.REJECTED:
                continue
            self.session.add(
                EffectiveUnit(unit_key=unit_key, decision_id=predecessor_id)
            )
            predecessor.status = DecisionStatus.EFFECTIVE
            # A current per-unit binding means the singular whole-record pointer
            # can no longer truthfully describe this multi-op decision.
            predecessor.superseded_by_decision_id = None
            restored_by_predecessor.setdefault(predecessor_id, []).append(unit_key)

        # Rows created before per-unit evidence used the singular back-pointer.
        if not displaced_units:
            predecessors = list(
                self.session.scalars(
                    select(Decision).where(
                        Decision.superseded_by_decision_id == rejected.id,
                        Decision.status == DecisionStatus.SUPERSEDED,
                    )
                )
            )
            for predecessor in predecessors:
                units = self.registry.derive_units(
                    [OpSpec.model_validate(op) for op in predecessor.ops],
                    stable_event_id=predecessor.stable_event_id
                    or str(predecessor.id),
                )
                for unit in units:
                    standing_unit: EffectiveUnit | None = self.session.get(
                        EffectiveUnit,
                        unit.unit_key,
                    )
                    if not unit.occupies or standing_unit is not None:
                        continue
                    self.session.add(
                        EffectiveUnit(
                            unit_key=unit.unit_key,
                            decision_id=predecessor.id,
                        )
                    )
                    restored_by_predecessor.setdefault(
                        predecessor.id, []
                    ).append(unit.unit_key)
                if predecessor.id in restored_by_predecessor:
                    predecessor.status = DecisionStatus.EFFECTIVE
                    predecessor.superseded_by_decision_id = None

        for predecessor_id, restored_units in sorted(
            restored_by_predecessor.items()
        ):
            append_event(
                self.session,
                context=context,
                kind="decision_effective",
                aggregate="decision",
                aggregate_id=predecessor_id,
                payload={
                    "decision_id": predecessor_id,
                    "resurrected_after": rejected.id,
                    "restored_units": sorted(restored_units),
                    "displacement_source_event_seq": (
                        effective_event.seq if effective_event is not None else None
                    ),
                },
                command_id=command_id,
            )
        return sorted(restored_by_predecessor)

    def _matching_proposal(self, units: list[DerivedUnit]) -> Decision | None:
        expected = self._unit_value_map(units)
        for proposal in self.session.scalars(
            select(Decision).where(Decision.status == DecisionStatus.PROPOSED)
        ):
            proposal_units = self.registry.derive_units(
                [OpSpec.model_validate(op) for op in proposal.ops],
                stable_event_id=proposal.stable_event_id or str(proposal.id),
            )
            if self._unit_value_map(proposal_units) == expected:
                return proposal
        return None

    def _matching_effective_decisions(
        self,
        units: list[DerivedUnit],
        bindings: dict[str, int],
    ) -> list[Decision] | None:
        occupied = [unit for unit in units if unit.occupies]
        if not occupied or any(
            unit.unit_key not in bindings for unit in occupied
        ):
            return None
        decisions = {
            decision.id: decision
            for decision in self._decisions_for_ids(set(bindings.values()))
        }
        for unit in occupied:
            standing = decisions[bindings[unit.unit_key]]
            standing_units = self.registry.derive_units(
                [OpSpec.model_validate(op) for op in standing.ops],
                stable_event_id=standing.stable_event_id or str(standing.id),
            )
            standing_map = self._unit_value_map(standing_units)
            if standing_map.get(unit.unit_key) != (
                unit.op,
                unit.canonical_value,
            ):
                return None
        return list(decisions.values())

    def _window_overlaps(
        self,
        units: list[DerivedUnit],
        effect_window: tuple,
    ) -> bool:
        unit_keys = {unit.unit_key for unit in units if unit.occupies}
        window_from, window_until = effect_window
        windows = self.session.scalars(
            select(Decision).where(
                Decision.status == DecisionStatus.EFFECTIVE,
                Decision.effect_window_from.is_not(None),
                Decision.effect_window_from < window_until,
                Decision.effect_window_until > window_from,
            )
        )
        for window in windows:
            window_units = self.registry.derive_units(
                [OpSpec.model_validate(op) for op in window.ops],
                stable_event_id=window.stable_event_id or str(window.id),
            )
            if unit_keys.intersection(
                unit.unit_key for unit in window_units if unit.occupies
            ):
                return True
        return False

    @staticmethod
    def _unit_value_map(
        units: list[DerivedUnit],
    ) -> dict[str, tuple[str, str]]:
        return {
            unit.unit_key: (unit.op, unit.canonical_value)
            for unit in units
            if unit.occupies
        }

    def _add_citations(
        self,
        decision_id: int,
        citations: list[CitationSpec],
        *,
        force_kind: CitationKind | None = None,
    ) -> None:
        existing_message_ids = set(
            self.session.scalars(
                select(DecisionCitation.message_id).where(
                    DecisionCitation.decision_id == decision_id
                )
            )
        )
        for citation in citations:
            if citation.message_id in existing_message_ids:
                continue
            self.session.add(
                DecisionCitation(
                    decision_id=decision_id,
                    message_id=citation.message_id,
                    kind=force_kind or citation.kind,
                    rev_at_capture=citation.rev_at_capture,
                    rev_at_act=citation.rev_at_act,
                )
            )
            existing_message_ids.add(citation.message_id)

    def _decisions_for_ids(self, decision_ids: set[int]) -> list[Decision]:
        if not decision_ids:
            return []
        return list(
            self.session.scalars(
                select(Decision)
                .where(Decision.id.in_(decision_ids))
                .order_by(Decision.id)
            )
        )

    def _effect(
        self,
        decision: Decision,
        *,
        units: list[DerivedUnit],
        predecessors: list[Decision],
        bindings: dict[str, int],
        context: HandleContext,
        command_id: str,
    ) -> None:
        predecessor_ids = {predecessor.id for predecessor in predecessors}
        if predecessors:
            decision.supersedes_decision_id = predecessors[0].id
        displaced_units = [
            {"unit_key": unit_key, "decision_id": predecessor_id}
            for unit_key, predecessor_id in sorted(bindings.items())
        ]
        for predecessor in predecessors:
            predecessor_unit_keys = {
                item["unit_key"]
                for item in displaced_units
                if item["decision_id"] == predecessor.id
            }
            if predecessor_unit_keys:
                self.session.execute(
                    delete(EffectiveUnit).where(
                        EffectiveUnit.decision_id == predecessor.id,
                        EffectiveUnit.unit_key.in_(predecessor_unit_keys),
                    )
                )
            has_unaffected_units = self.session.scalar(
                select(EffectiveUnit.unit_key)
                .where(EffectiveUnit.decision_id == predecessor.id)
                .limit(1)
            )
            if has_unaffected_units is None:
                predecessor.status = DecisionStatus.SUPERSEDED
                predecessor.superseded_by_decision_id = decision.id
            append_event(
                self.session,
                context=context,
                kind="decision_superseded",
                aggregate="decision",
                aggregate_id=predecessor.id,
                payload={
                    "decision_id": predecessor.id,
                    "superseded_by": decision.id,
                    "displaced_units": sorted(predecessor_unit_keys),
                    "partial": has_unaffected_units is not None,
                },
                command_id=command_id,
            )
        occupied_keys = {unit.unit_key for unit in units if unit.occupies}
        for proposal in self._overlapping_proposals(
            occupied_keys, exclude_id=decision.id
        ):
            proposal.status = DecisionStatus.REJECTED
            proposal.rejected_reason = RejectedReason.OVERRULED
            proposal.superseded_by_decision_id = decision.id
            append_event(
                self.session,
                context=context,
                kind="decision_rejected",
                aggregate="decision",
                aggregate_id=proposal.id,
                payload={
                    "decision_id": proposal.id,
                    "reason": RejectedReason.OVERRULED.value,
                    "superseded_by": decision.id,
                },
                command_id=command_id,
            )
        self.session.add_all(
            [
                EffectiveUnit(unit_key=unit_key, decision_id=decision.id)
                for unit_key in occupied_keys
            ]
        )
        append_event(
            self.session,
            context=context,
            kind="decision_effective",
            aggregate="decision",
            aggregate_id=decision.id,
            payload={
                "decision_id": decision.id,
                "status": DecisionStatus.EFFECTIVE.value,
                "ops": decision.ops,
                "supersedes": sorted(predecessor_ids),
                "displaced_units": displaced_units,
            },
            command_id=command_id,
        )

    def _overlapping_proposals(
        self,
        unit_keys: set[str],
        *,
        exclude_id: int,
    ) -> list[Decision]:
        proposals = self.session.scalars(
            select(Decision).where(
                Decision.status == DecisionStatus.PROPOSED,
                Decision.id != exclude_id,
            )
        )
        overlapping: list[Decision] = []
        for proposal in proposals:
            proposal_units = self.registry.derive_units(
                [OpSpec.model_validate(op) for op in proposal.ops],
                stable_event_id=proposal.stable_event_id or str(proposal.id),
            )
            if unit_keys.intersection(
                unit.unit_key for unit in proposal_units if unit.occupies
            ):
                overlapping.append(proposal)
        return overlapping
