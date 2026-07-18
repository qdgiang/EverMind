"""Authority, task-state, and cross-project transfer policy for decision writes."""

from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from evermind.contracts.enums import ProjectStatus, TaskStatus
from evermind.decisions.authority import AuthorityComparison, AuthorityResolver
from evermind.decisions.facets import DerivedUnit, FacetRegistry
from evermind.decisions.models import Decision, DecisionTask, ProcessedCommand
from evermind.org.service import OrgService


class DecisionPolicy:
    def __init__(
        self,
        session: Session,
        *,
        org: OrgService,
        authority: AuthorityResolver,
        registry: FacetRegistry,
    ):
        self.session = session
        self.org = org
        self.authority = authority
        self.task_state = authority.task_state
        self.registry = registry

    def _actor_can_effect(
        self,
        actor_user_id: int,
        units: list[DerivedUnit],
        predecessors: list[Decision],
        *,
        maker_user_id: int,
        approval: bool,
    ) -> bool:
        transfers = self._transfer_requirements(units)
        if transfers:
            if not self._can_effect_transfers(
                actor_user_id,
                maker_user_id=maker_user_id,
                transfers=transfers,
                approval=approval,
            ):
                return False
            non_transfer_units = [
                unit for unit in units if not self._is_project_transfer(unit)
            ]
            if not all(
                self._can_decide_unit(actor_user_id, unit)
                or self._can_decide_unit(maker_user_id, unit)
                for unit in non_transfer_units
            ):
                return False
            authority_rank = max(
                self.org.rank_of(actor_user_id),
                self.org.rank_of(maker_user_id),
            )
            return all(
                predecessor.decided_by_role_at_time <= authority_rank
                for predecessor in predecessors
            )
        if not all(self._can_decide_unit(actor_user_id, unit) for unit in units):
            return False
        allowed = {AuthorityComparison.GREATER, AuthorityComparison.EQUAL}
        return all(
            self.authority.compare_to_snapshot(
                actor_user_id,
                predecessor.decided_by_user_id,
                predecessor.decided_by_role_at_time,
            )
            in allowed
            for predecessor in predecessors
        )

    def _hold_reason(
        self,
        actor_user_id: int,
        units: list[DerivedUnit],
        predecessors: list[Decision],
        *,
        maker_user_id: int,
    ) -> str:
        if self._transfer_requirements(units) and self.org.rank_of(actor_user_id) < 3:
            return "two_key_transfer"
        if not all(self._can_decide_unit(actor_user_id, unit) for unit in units):
            return "authority"
        comparisons = {
            self.authority.compare_to_snapshot(
                actor_user_id,
                predecessor.decided_by_user_id,
                predecessor.decided_by_role_at_time,
            )
            for predecessor in predecessors
        }
        if AuthorityComparison.INCOMPARABLE in comparisons:
            return "peer_conflict"
        return "rank_gate"

    def _required_approvers(
        self,
        maker_user_id: int,
        units: list[DerivedUnit],
    ) -> set[int]:
        transfers = self._transfer_requirements(units)
        if not transfers:
            return self.authority.required_approver_ids(
                [unit.unit_key for unit in units]
            )
        source_project_id, destination_project_id = transfers[0]
        source_leads = self.org.lead_user_ids_for_project(source_project_id)
        destination_leads = self.org.lead_user_ids_for_project(destination_project_id)
        maker_is_source = maker_user_id in source_leads
        maker_is_destination = maker_user_id in destination_leads
        if maker_is_source and not maker_is_destination:
            opposite_leads = destination_leads - {maker_user_id}
        elif maker_is_destination and not maker_is_source:
            opposite_leads = source_leads - {maker_user_id}
        else:
            opposite_leads = set()
        non_transfer_units = [
            unit for unit in units if not self._is_project_transfer(unit)
        ]
        sufficient_opposite_leads = {
            lead_user_id
            for lead_user_id in opposite_leads
            if all(
                self._can_decide_unit(maker_user_id, unit)
                or self._can_decide_unit(lead_user_id, unit)
                for unit in non_transfer_units
            )
        }
        if sufficient_opposite_leads:
            return sufficient_opposite_leads
        return self.org.coordinator_user_ids() - {maker_user_id}

    def _can_effect_transfers(
        self,
        actor_user_id: int,
        *,
        maker_user_id: int,
        transfers: list[tuple[int, int]],
        approval: bool,
    ) -> bool:
        if self.org.rank_of(actor_user_id) >= 3:
            return True
        if not approval or actor_user_id == maker_user_id or len(transfers) != 1:
            return False
        source_project_id, destination_project_id = transfers[0]
        source_leads = self.org.lead_user_ids_for_project(source_project_id)
        destination_leads = self.org.lead_user_ids_for_project(destination_project_id)
        maker_is_source = maker_user_id in source_leads
        maker_is_destination = maker_user_id in destination_leads
        if maker_is_source == maker_is_destination:
            return False
        return (
            actor_user_id in destination_leads
            if maker_is_source
            else actor_user_id in source_leads
        )

    def _task_versions(self, units: list[DerivedUnit]) -> dict[str, str]:
        versions: dict[str, str] = {}
        for task_id in self._task_ids(units):
            task = self.task_state.get_task(task_id)
            if task is not None:
                versions[str(task_id)] = task.current_version
        return versions

    def _revalidate_tasks(
        self,
        decision: Decision,
        units: list[DerivedUnit],
    ) -> dict | None:
        basis = self._proposal_task_versions(decision.id)
        for task_id in self._task_ids(units):
            task = self.task_state.get_task(task_id)
            if task is None:
                return {
                    "ok": False,
                    "status": "revalidation_required",
                    "http_status": 409,
                    "decision_id": decision.id,
                    "reason": "target_missing",
                }
            if task.status is TaskStatus.MERGED:
                return {
                    "ok": False,
                    "status": "redirect_required",
                    "http_status": 409,
                    "decision_id": decision.id,
                    "merged_survivor": task.merged_survivor,
                    "current_task_version": task.current_version,
                }
            if task.status is TaskStatus.CANCELED:
                return {
                    "ok": False,
                    "status": "revalidation_required",
                    "http_status": 409,
                    "decision_id": decision.id,
                    "reason": "terminal:canceled",
                    "current_task_version": task.current_version,
                }
            prior_version = basis.get(str(task_id))
            if prior_version is not None and prior_version != task.current_version:
                return {
                    "ok": False,
                    "status": "revalidation_required",
                    "http_status": 409,
                    "decision_id": decision.id,
                    "reason": "task_version_changed",
                    "current_task_version": task.current_version,
                }
        return None

    def _proposal_task_versions(self, decision_id: int) -> dict[str, str]:
        for outcome in self.session.scalars(select(ProcessedCommand.outcome)):
            if outcome.get("decision_id") == decision_id and "task_versions" in outcome:
                return dict(outcome["task_versions"])
        return {}

    @classmethod
    def _task_ids(cls, units: list[DerivedUnit]) -> set[int]:
        task_ids = {
            int(unit.target.removeprefix("task:"))
            for unit in units
            if unit.target.startswith("task:")
            and unit.target.removeprefix("task:").isdecimal()
        }
        task_ids.update(
            task_id
            for unit in units
            if (task_id := cls._merge_absorbed_task_id(unit)) is not None
        )
        return task_ids

    def _can_decide_unit(self, actor_user_id: int, unit: DerivedUnit) -> bool:
        absorbed_task_id = self._merge_absorbed_task_id(unit)
        if absorbed_task_id is None:
            return self.authority.can_decide(actor_user_id, unit.unit_key)
        return self.authority.can_decide(actor_user_id, unit.unit_key) or (
            self.authority.can_decide(
                actor_user_id,
                f"v1|task:{absorbed_task_id}|merge",
            )
        )

    def _lock_targets(self, units: list[DerivedUnit]) -> set[str]:
        targets = {unit.target for unit in units}
        targets.update(
            f"task:{task_id}"
            for unit in units
            if (task_id := self._merge_absorbed_task_id(unit)) is not None
        )
        for source_project_id, destination_project_id in self._transfer_requirements(
            units
        ):
            targets.update(
                {
                    f"project:{source_project_id}",
                    f"project:{destination_project_id}",
                }
            )
        return targets

    def _validate_related_targets(self, units: list[DerivedUnit]) -> None:
        transfers = self._transfer_requirements(units)
        if len(transfers) > 1:
            raise ValueError("a decision may contain only one project transfer")
        for unit in units:
            if unit.facet == "merge" and self._merge_absorbed_task_id(unit) is None:
                raise ValueError("merge requires an absorbed task target")
        for source_project_id, destination_project_id in transfers:
            if source_project_id == destination_project_id:
                raise ValueError("project transfer destination must differ from source")
            destination = self.org.get_project(destination_project_id)
            if destination is None:
                raise ValueError("destination project does not exist")
            if destination.status is not ProjectStatus.ACTIVE:
                raise ValueError("destination project must be active")

    def _validate_current_tasks(self, units: list[DerivedUnit]) -> dict | None:
        for task_id in sorted(self._task_ids(units)):
            task = self.task_state.get_task(task_id)
            if task is None:
                return {
                    "ok": False,
                    "status": "revalidation_required",
                    "http_status": 409,
                    "reason": "target_missing",
                    "task_id": task_id,
                }
            if task.status is TaskStatus.MERGED:
                return {
                    "ok": False,
                    "status": "redirect_required",
                    "http_status": 409,
                    "task_id": task_id,
                    "merged_survivor": task.merged_survivor,
                    "current_task_version": task.current_version,
                }
            if task.status is TaskStatus.CANCELED:
                return {
                    "ok": False,
                    "status": "revalidation_required",
                    "http_status": 409,
                    "reason": "terminal:canceled",
                    "task_id": task_id,
                    "current_task_version": task.current_version,
                }
        return None

    def _transfer_requirements(
        self,
        units: list[DerivedUnit],
    ) -> list[tuple[int, int]]:
        transfers: list[tuple[int, int]] = []
        for unit in units:
            if unit.facet != "project" or not unit.target.startswith("task:"):
                continue
            task_id_text = unit.target.removeprefix("task:")
            if not task_id_text.isdecimal():
                raise ValueError("project transfer requires a task target")
            task = self.task_state.get_task(int(task_id_text))
            if task is None:
                continue
            destination_project_id = self._project_id_from_value(unit.canonical_value)
            if destination_project_id is None:
                raise ValueError("project transfer requires a destination project")
            transfers.append((task.project_id, destination_project_id))
        return transfers

    @staticmethod
    def _project_id_from_value(canonical_value: str) -> int | None:
        value = json.loads(canonical_value)
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            raw_id = value.removeprefix("project:")
            return int(raw_id) if raw_id.isdecimal() else None
        if isinstance(value, dict):
            dict_project_id = value.get(
                "destination_project_id",
                value.get("project_id"),
            )
            if isinstance(dict_project_id, int):
                return dict_project_id
            if isinstance(dict_project_id, str) and dict_project_id.isdecimal():
                return int(dict_project_id)
        return None

    @staticmethod
    def _is_project_transfer(unit: DerivedUnit) -> bool:
        return unit.facet == "project" and unit.target.startswith("task:")

    @staticmethod
    def _merge_absorbed_task_id(unit: DerivedUnit) -> int | None:
        if unit.facet != "merge":
            return None
        value = json.loads(unit.canonical_value)
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.startswith("task:"):
            raw_id = value.removeprefix("task:")
            return int(raw_id) if raw_id.isdecimal() else None
        if isinstance(value, dict):
            related_id = value.get("absorbed_task_id", value.get("task_id"))
            if isinstance(related_id, int):
                return related_id
            if isinstance(related_id, str) and related_id.isdecimal():
                return int(related_id)
        return None

    def _add_task_links(self, decision_id: int, units: list[DerivedUnit]) -> None:
        task_ids = self._task_ids(units)
        self.session.add_all(
            [
                DecisionTask(decision_id=decision_id, task_id=task_id)
                for task_id in task_ids
            ]
        )
