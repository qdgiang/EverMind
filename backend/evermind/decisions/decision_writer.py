"""Command orchestration for decision proposal, approval, and rejection."""

from __future__ import annotations

from sqlalchemy import delete

from evermind.contracts.commands import (
    ApproveProposal,
    OpSpec,
    ProposeDecision,
    RejectProposal,
)
from evermind.contracts.enums import (
    ApprovalVia,
    CitationKind,
    CreatedFrom,
    DecisionStatus,
    RejectedReason,
)
from evermind.decisions.authority import AuthorityComparison
from evermind.decisions.decision_lifecycle import DecisionLifecycle
from evermind.decisions.models import (
    Decision,
    EffectiveUnit,
)
from evermind.decisions.ordering import HandleContext
from evermind.decisions.persistence import (
    append_event,
    current_bindings_for_units,
    current_version,
    serialize_targets,
)


class DecisionWriter(DecisionLifecycle):
    def propose(self, command: ProposeDecision, context: HandleContext) -> dict:
        if (
            command.effect_window is not None
            and command.effect_window[0] >= command.effect_window[1]
        ):
            raise ValueError("effect_window requires from < until")
        if command.created_from is CreatedFrom.LLM and (
            command.source_message_id is None
            or command.window_id is None
            or command.confidence is None
        ):
            raise ValueError("LLM decisions require source_message_id, window_id, and confidence")
        units = self.registry.derive_units(
            command.ops,
            stable_event_id=context.stable_event_id,
        )
        serialize_targets(self.session, self._lock_targets(units))
        self._validate_related_targets(units)
        target_revalidation = self._validate_current_tasks(units)
        if target_revalidation is not None:
            return target_revalidation
        occupied_keys = {unit.unit_key for unit in units if unit.occupies}
        bindings = current_bindings_for_units(self.session, units)
        predecessors = self._decisions_for_ids(set(bindings.values()))
        chronology_predecessors = [] if command.effect_window is not None else predecessors
        chronology = self._chronology_state(context, chronology_predecessors)
        chat_origin = command.created_from in {
            CreatedFrom.MARKER,
            CreatedFrom.LLM,
            CreatedFrom.TRANSCRIPT,
        }
        if chat_origin and not command.citations:
            raise ValueError("chat-originated decisions require evidence citations")
        cited_authors = set(context.citation_authors.values())
        maker_is_cited = not chat_origin or command.decided_by_user_id in cited_authors
        delegated_by = context.delegated_by_user_id
        delegation_is_cited = delegated_by is not None and delegated_by in cited_authors
        window_overlap = command.effect_window is not None and self._window_overlaps(
            units,
            command.effect_window,
        )
        confidence_allows = (
            command.created_from is not CreatedFrom.LLM
            or command.confidence is not None
            and command.confidence >= 0.8
        )
        authority_actor = None
        candidates = ([command.decided_by_user_id] if maker_is_cited else []) + (
            [delegated_by] if delegation_is_cited and delegated_by is not None else []
        )
        authority_predecessors = chronology_predecessors
        if confidence_allows and not window_overlap:
            authority_actor = next(
                (
                    candidate
                    for candidate in candidates
                    if self._actor_can_effect(
                        candidate,
                        units,
                        authority_predecessors,
                        maker_user_id=command.decided_by_user_id,
                        approval=False,
                    )
                ),
                None,
            )
        authorized = authority_actor is not None
        effective = authorized and chronology == "current"
        merged_proposal = self._matching_proposal(units) if chronology == "current" else None
        if merged_proposal is not None and not effective:
            self._add_citations(merged_proposal.id, command.citations)
            append_event(
                self.session,
                context=context,
                kind="corroboration_appended",
                aggregate="decision",
                aggregate_id=merged_proposal.id,
                payload={"decision_id": merged_proposal.id, "proposal_merged": True},
                command_id=str(command.client_command_id),
            )
            return {
                "ok": True,
                "status": "proposal_merged",
                "decision_id": merged_proposal.id,
                "version": current_version(self.session, occupied_keys),
            }
        matching_effective = (
            None
            if command.effect_window is not None or chronology != "current"
            else self._matching_effective_decisions(units, bindings)
        )
        if matching_effective is not None:
            for standing in matching_effective:
                self._add_citations(
                    standing.id,
                    command.citations,
                    force_kind=CitationKind.CORROBORATION,
                )
                append_event(
                    self.session,
                    context=context,
                    kind="corroboration_appended",
                    aggregate="decision",
                    aggregate_id=standing.id,
                    payload={"decision_id": standing.id, "same_value": True},
                    command_id=str(command.client_command_id),
                )
            decision_ids = sorted(decision.id for decision in matching_effective)
            return {
                "ok": True,
                "status": "corroborated",
                "decision_id": decision_ids[0],
                "decision_ids": decision_ids,
                "version": current_version(self.session, occupied_keys),
            }
        status = (
            DecisionStatus.SUPERSEDED
            if authorized and chronology == "late"
            else DecisionStatus.EFFECTIVE
            if effective
            else DecisionStatus.PROPOSED
        )
        rank = self.org.rank_of(command.decided_by_user_id)
        confidence = (
            1.0
            if command.created_from
            in {
                CreatedFrom.DASHBOARD,
                CreatedFrom.MARKER,
            }
            else command.confidence
        )
        decision = Decision(
            ts=context.event_ts,
            recorded_at=context.recorded_at,
            decided_by_user_id=command.decided_by_user_id,
            decided_by_role_at_time=rank,
            scope=command.scope,
            scope_target=command.scope_target,
            description=command.description,
            context=command.context,
            note=None,
            ops=[op.model_dump(mode="json") for op in command.ops],
            effect_window_from=command.effect_window[0] if command.effect_window else None,
            effect_window_until=command.effect_window[1] if command.effect_window else None,
            status=status,
            rejected_reason=None,
            supersedes_decision_id=None,
            superseded_by_decision_id=(
                predecessors[0].id if status is DecisionStatus.SUPERSEDED else None
            ),
            approved_by_user_id=authority_actor if authorized else None,
            approval_via=(
                ApprovalVia.DELEGATION
                if authorized and authority_actor != command.decided_by_user_id
                else ApprovalVia.AUTHORITY
                if authorized
                else None
            ),
            approved_by_role_at_act=(
                self.org.rank_of(authority_actor)
                if authorized and authority_actor is not None
                else None
            ),
            created_from=command.created_from,
            confidence=confidence,
            window_id=command.window_id,
            stable_event_id=context.stable_event_id,
        )
        self.session.add(decision)
        self.session.flush()
        self._add_task_links(decision.id, units)
        self._add_citations(decision.id, command.citations)
        if effective and command.effect_window is None:
            self._effect(
                decision,
                units=units,
                predecessors=predecessors,
                bindings=bindings,
                context=context,
                command_id=str(command.client_command_id),
            )
        self.session.flush()
        if not effective or command.effect_window is not None:
            append_event(
                self.session,
                context=context,
                kind=(
                    "decision_superseded"
                    if status is DecisionStatus.SUPERSEDED
                    else "decision_effective"
                    if effective
                    else "decision_proposed"
                ),
                aggregate="decision",
                aggregate_id=decision.id,
                payload={
                    "decision_id": decision.id,
                    "status": status.value,
                    "ops": decision.ops,
                },
                command_id=str(command.client_command_id),
            )
        outcome: dict[str, object] = {
            "ok": True,
            "status": status.value,
            "decision_id": decision.id,
            "version": current_version(self.session, occupied_keys),
        }
        if window_overlap:
            outcome["hold_reason"] = "window_overlap"
        elif chronology == "conflict":
            outcome["hold_reason"] = "chronology_conflict"
        elif status is DecisionStatus.SUPERSEDED:
            outcome["late_arrival"] = True
        elif not effective and candidates:
            hold_reason = self._hold_reason(
                candidates[0],
                units,
                authority_predecessors,
                maker_user_id=command.decided_by_user_id,
            )
            outcome["hold_reason"] = hold_reason
            required = self._required_approvers(command.decided_by_user_id, units)
            required.update(
                predecessor.decided_by_user_id for predecessor in authority_predecessors
            )
            outcome["required_approver_ids"] = sorted(required)
        if status is DecisionStatus.PROPOSED:
            outcome["task_versions"] = self._task_versions(units)
        return outcome

    def approve(self, command: ApproveProposal, context: HandleContext) -> dict:
        decision = self.session.get(Decision, command.decision_id)
        if decision is None:
            return {"ok": False, "status": "not_found", "http_status": 404}
        units = self.registry.derive_units(
            [OpSpec.model_validate(op) for op in decision.ops],
            stable_event_id=decision.stable_event_id or str(decision.id),
        )
        serialize_targets(self.session, self._lock_targets(units))
        self.session.refresh(decision)
        if decision.status is not DecisionStatus.PROPOSED:
            return {
                "ok": False,
                "status": "conflict",
                "http_status": 409,
                "decision_id": decision.id,
                "current_status": decision.status.value,
            }
        self._validate_related_targets(units)
        revalidation = self._revalidate_tasks(decision, units)
        if revalidation is not None:
            return revalidation
        if (
            decision.effect_window_from is not None
            and decision.effect_window_until is not None
            and self._window_overlaps(
                units,
                (decision.effect_window_from, decision.effect_window_until),
            )
        ):
            return {
                "ok": False,
                "status": "window_overlap",
                "http_status": 409,
                "decision_id": decision.id,
            }
        occupied_keys = {unit.unit_key for unit in units if unit.occupies}
        bindings = current_bindings_for_units(self.session, units)
        predecessors = self._decisions_for_ids(set(bindings.values()))
        if not self._actor_can_effect(
            command.approved_by_user_id,
            units,
            predecessors,
            maker_user_id=decision.decided_by_user_id,
            approval=True,
        ):
            return {
                "ok": False,
                "status": "authority_required",
                "http_status": 403,
                "decision_id": decision.id,
            }
        rank = self.org.rank_of(command.approved_by_user_id)
        decision.status = DecisionStatus.EFFECTIVE
        decision.approved_by_user_id = command.approved_by_user_id
        decision.approval_via = (
            ApprovalVia.SELF_CONFIRM
            if command.approved_by_user_id == decision.decided_by_user_id
            else ApprovalVia.AUTHORITY
        )
        decision.approved_by_role_at_act = rank
        if decision.effect_window_from is None:
            self._effect(
                decision,
                units=units,
                predecessors=predecessors,
                bindings=bindings,
                context=context,
                command_id=str(command.client_command_id),
            )
        else:
            append_event(
                self.session,
                context=context,
                kind="decision_effective",
                aggregate="decision",
                aggregate_id=decision.id,
                payload={"decision_id": decision.id, "status": "effective", "ops": decision.ops},
                command_id=str(command.client_command_id),
            )
        self.session.flush()
        return {
            "ok": True,
            "status": "effective",
            "decision_id": decision.id,
            "version": current_version(self.session, occupied_keys),
        }

    def reject(self, command: RejectProposal, context: HandleContext) -> dict:
        decision = self.session.get(Decision, command.decision_id)
        if decision is None:
            return {"ok": False, "status": "not_found", "http_status": 404}
        units = self.registry.derive_units(
            [OpSpec.model_validate(op) for op in decision.ops],
            stable_event_id=decision.stable_event_id or str(decision.id),
        )
        serialize_targets(self.session, self._lock_targets(units))
        self.session.refresh(decision)
        if decision.status is DecisionStatus.REJECTED:
            return {
                "ok": False,
                "status": "conflict",
                "http_status": 409,
                "decision_id": decision.id,
                "current_status": decision.status.value,
            }
        comparison = self.authority.compare_to_snapshot(
            command.rejected_by_user_id,
            decision.decided_by_user_id,
            decision.decided_by_role_at_time,
        )
        rejector_is_active = self.org.rank_of(command.rejected_by_user_id) > 0
        may_reject = rejector_is_active and (
            command.rejected_by_user_id == decision.decided_by_user_id
            or comparison in {AuthorityComparison.GREATER, AuthorityComparison.EQUAL}
        )
        self._validate_related_targets(units)
        occupied_keys = {unit.unit_key for unit in units if unit.occupies}
        if not may_reject:
            append_event(
                self.session,
                context=context,
                kind="decision_rejected",
                aggregate="decision",
                aggregate_id=decision.id,
                payload={
                    "decision_id": decision.id,
                    "applied": False,
                    "outcome": "challenge_required",
                    "challenged_by": command.rejected_by_user_id,
                },
                command_id=str(command.client_command_id),
            )
            return {
                "ok": True,
                "status": "challenge_required",
                "applied": False,
                "decision_id": decision.id,
                "version": current_version(self.session, occupied_keys),
            }
        was_proposed = decision.status is DecisionStatus.PROPOSED
        decision.status = DecisionStatus.REJECTED
        decision.rejected_reason = (
            RejectedReason.WITHDRAWN
            if was_proposed and command.rejected_by_user_id == decision.decided_by_user_id
            else RejectedReason(command.reason)
        )
        self.session.execute(delete(EffectiveUnit).where(EffectiveUnit.decision_id == decision.id))
        append_event(
            self.session,
            context=context,
            kind="decision_rejected",
            aggregate="decision",
            aggregate_id=decision.id,
            payload={
                "decision_id": decision.id,
                "applied": True,
                "reason": decision.rejected_reason.value,
                "rejected_by": command.rejected_by_user_id,
            },
            command_id=str(command.client_command_id),
        )
        resurrected = self._resurrect_predecessors(
            decision,
            context=context,
            command_id=str(command.client_command_id),
        )
        self.session.flush()
        return {
            "ok": True,
            "status": "rejected",
            "decision_id": decision.id,
            "resurrected_decision_ids": resurrected,
            "version": current_version(self.session, occupied_keys),
        }
