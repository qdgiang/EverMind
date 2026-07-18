from __future__ import annotations

from importlib import import_module
from uuid import UUID

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from evermind.contracts.commands import OpSpec, ProposeDecision
from evermind.contracts.enums import CreatedFrom, DecisionScope, DecisionStatus, TaskStatus
from evermind.decisions.facets import version_for_bindings
from evermind.decisions.service import DecisionsService
from evermind.decisions.models import Decision, EffectiveUnit
from evermind.decisions.task_state import TaskStateView
from tests.scenarios.test_lifecycle_basics import _context, _seed_org


def test_facet_registry_derives_scope_slots_edges_and_append_units() -> None:
    """S1/S7: DEC-2 units are data-driven across task, team, and project scopes."""
    facets = import_module("evermind.decisions.facets")
    registry = facets.FacetRegistry.default()

    field = registry.derive_units(
        [OpSpec(target="task:1", facet="description", op="set", value="Peaches")],
        stable_event_id="evt-a",
    )
    policy = registry.derive_units(
        [OpSpec(target="team:4", facet="attr:entry-fee", op="set", value="free")],
        stable_event_id="evt-b",
    )
    assignment_add = registry.derive_units(
        [OpSpec(target="task:1", facet="assignment", op="add", value=8)],
        stable_event_id="evt-c",
    )
    assignment_remove = registry.derive_units(
        [OpSpec(target="task:1", facet="assignment", op="remove", value=8)],
        stable_event_id="evt-d",
    )
    other_assignment = registry.derive_units(
        [OpSpec(target="task:1", facet="assignment", op="add", value=9)],
        stable_event_id="evt-e",
    )
    dependency_add = registry.derive_units(
        [OpSpec(target="task:1", facet="dependency", op="add", value="task:2")],
        stable_event_id="evt-f",
    )
    dependency_remove = registry.derive_units(
        [OpSpec(target="task:1", facet="dependency", op="remove", value="task:2")],
        stable_event_id="evt-g",
    )
    first_note = registry.derive_units(
        [OpSpec(target="project:3", facet="note", op="append", value="Bring receipts")],
        stable_event_id="evt-h",
    )
    second_note = registry.derive_units(
        [OpSpec(target="project:3", facet="note", op="append", value="Bring receipts")],
        stable_event_id="evt-i",
    )

    assert field[0].unit_key == "v1|task:1|description"
    assert policy[0].unit_key == "v1|team:4|attr:entry-fee"
    assert assignment_add[0].unit_key == assignment_remove[0].unit_key
    assert assignment_add[0].unit_key != other_assignment[0].unit_key
    assert dependency_add[0].unit_key == dependency_remove[0].unit_key
    assert first_note[0].occupies is False
    assert first_note[0].unit_key != second_note[0].unit_key


def test_facet_registry_validates_ops_and_versions_deterministically() -> None:
    """DEC-2/EVM-021: invalid ops fail closed and version order is deterministic."""
    facets = import_module("evermind.decisions.facets")
    registry = facets.FacetRegistry.default()

    ops = [
        OpSpec(target="task:7", facet="team", op="add", value=3),
        OpSpec(target="task:7", facet="attr:venue", op="set", value={"room": "A"}),
    ]
    first = registry.derive_units(ops, stable_event_id="evt-1")
    second = registry.derive_units(list(reversed(ops)), stable_event_id="evt-1")

    assert {unit.unit_key for unit in first} == {unit.unit_key for unit in second}
    assert facets.version_for_bindings({"unit-b": 2, "unit-a": 1}) == (
        facets.version_for_bindings({"unit-a": 1, "unit-b": 2})
    )
    assert facets.version_for_bindings({"unit-a": 1}).startswith("v1:")

    with pytest.raises(ValueError, match="unsupported op"):
        registry.derive_units(
            [OpSpec(target="task:7", facet="status", op="append", value="done")],
            stable_event_id="evt-2",
        )
    with pytest.raises(ValueError, match="unsupported facet"):
        registry.derive_units(
            [OpSpec(target="task:7", facet="unknown", op="set", value="x")],
            stable_event_id="evt-3",
        )


def test_team_project_and_teamless_policy_writes_route_to_total_authority(
    db_session: Session,
) -> None:
    """S7/G26/G48: policies are first-class and project holds route to coordinators."""
    _seed_org(db_session)

    class PolicyTaskPort:
        task = TaskStateView(
            id=502,
            project_id=101,
            status=TaskStatus.TODO,
            pic_user_ids=frozenset(),
            owning_team_ids=frozenset(),
            merged_into=None,
            current_version="task-v1",
        )

        def get_task(self, task_id: int):
            return self.task if task_id == 502 else None

    service = DecisionsService(db_session, task_state=PolicyTaskPort())

    def proposal(
        command_id: str,
        *,
        persona: str,
        actor: int,
        scope: DecisionScope,
        target: str,
        facet: str,
    ) -> ProposeDecision:
        return ProposeDecision(
            client_command_id=UUID(command_id),
            persona=persona,
            created_from=CreatedFrom.DASHBOARD,
            decided_by_user_id=actor,
            scope=scope,
            scope_target=target,
            description=facet,
            ops=[OpSpec(target=target, facet=facet, op="set", value="yes")],
            citations=[],
        )

    team_policy = service.handle(
        proposal(
            "00000000-0000-0000-0000-000000000111",
            persona="joe",
            actor=302,
            scope=DecisionScope.TEAM,
            target="team:201",
            facet="attr:class-schedule",
        ),
        context=_context(event_id="evt-team-policy", hour=9),
    )
    project_hold = service.handle(
        proposal(
            "00000000-0000-0000-0000-000000000112",
            persona="joe",
            actor=302,
            scope=DecisionScope.PROJECT,
            target="project:101",
            facet="attr:donation-method",
        ),
        context=_context(event_id="evt-project-hold", hour=10),
    )
    project_policy = service.handle(
        proposal(
            "00000000-0000-0000-0000-000000000113",
            persona="an",
            actor=301,
            scope=DecisionScope.PROJECT,
            target="project:101",
            facet="attr:donation-method",
        ),
        context=_context(event_id="evt-project-policy", hour=11),
    )
    teamless_task = service.handle(
        proposal(
            "00000000-0000-0000-0000-000000000114",
            persona="joe",
            actor=302,
            scope=DecisionScope.TASK,
            target="task:502",
            facet="attr:venue",
        ),
        context=_context(event_id="evt-teamless", hour=12),
    )

    assert team_policy["status"] == "effective"
    assert project_hold["status"] == "proposed"
    assert project_hold["required_approver_ids"] == [301]
    assert project_policy["status"] == "effective"
    assert teamless_task["status"] == "effective"


def test_assignment_slot_add_set_and_remove_follow_registry_conflict_rules(
    db_session: Session,
) -> None:
    """S1/G1: adds coexist by slot, set clears prior slots, remove replaces its add."""
    _seed_org(db_session)

    class AssignmentTaskPort:
        task = TaskStateView(
            id=501,
            project_id=101,
            status=TaskStatus.TODO,
            pic_user_ids=frozenset(),
            owning_team_ids=frozenset({201}),
            merged_into=None,
            current_version="task-v1",
        )

        def get_task(self, task_id: int):
            return self.task if task_id == 501 else None

    service = DecisionsService(db_session, task_state=AssignmentTaskPort())

    def assignment(
        command_id: str,
        op: str,
        value,
        *,
        expected_version: str | None = None,
    ) -> dict:
        return service.handle(
            ProposeDecision(
                client_command_id=UUID(command_id),
                persona="joe",
                expected_version=expected_version,
                created_from=CreatedFrom.DASHBOARD,
                decided_by_user_id=302,
                scope=DecisionScope.TASK,
                scope_target="task:501",
                description=f"assignment {op}",
                ops=[OpSpec(target="task:501", facet="assignment", op=op, value=value)],
                citations=[],
            ),
            context=_context(event_id=f"evt-{command_id[-3:]}", hour=13),
        )

    add_eight = assignment("00000000-0000-0000-0000-000000000115", "add", 8)
    add_nine = assignment("00000000-0000-0000-0000-000000000116", "add", 9)
    current_assignment_version = version_for_bindings(
        {
            unit.unit_key: unit.decision_id
            for unit in db_session.scalars(select(EffectiveUnit))
        }
    )
    set_ten = assignment(
        "00000000-0000-0000-0000-000000000117",
        "set",
        [10],
        expected_version=current_assignment_version,
    )
    add_eleven = assignment("00000000-0000-0000-0000-000000000118", "add", 11)
    remove_eleven = assignment(
        "00000000-0000-0000-0000-000000000119",
        "remove",
        11,
        expected_version=add_eleven["version"],
    )

    assert db_session.get(Decision, add_eight["decision_id"]).status is DecisionStatus.SUPERSEDED
    assert db_session.get(Decision, add_nine["decision_id"]).status is DecisionStatus.SUPERSEDED
    assert db_session.get(Decision, set_ten["decision_id"]).status is DecisionStatus.EFFECTIVE
    assert db_session.get(Decision, add_eleven["decision_id"]).status is DecisionStatus.SUPERSEDED
    assert db_session.get(Decision, remove_eleven["decision_id"]).status is DecisionStatus.EFFECTIVE
    assert len(list(db_session.scalars(select(EffectiveUnit)))) == 2
