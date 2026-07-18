from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import os
from threading import Barrier
from uuid import UUID

import pytest
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.orm import Session

from evermind.contracts.commands import (
    ApproveProposal,
    CitationSpec,
    OpSpec,
    ProposeDecision,
    RecordSignal,
    RecordTaskUpdate,
    RejectProposal,
)
from evermind.contracts.enums import (
    CreatedFrom,
    CitationKind,
    DecisionScope,
    DecisionStatus,
    ProjectKind,
    ProjectStatus,
    TaskStatus,
    UserStatus,
)
from evermind.db.eventlog import DomainEvent
from evermind.decisions.facets import version_for_bindings
from evermind.decisions.models import Decision, EffectiveUnit, ProcessedCommand
from evermind.decisions.service import DecisionsService
from evermind.decisions.task_state import TaskStateView
from evermind.decisions import gateway as gateway_module
from evermind.org.models import Project, Team, User, UserTeam
from evermind.org.service import OrgService
from tests.scenarios.test_lifecycle_basics import (
    FakeTaskStatePort,
    _context,
    _propose,
    _seed_org,
)


def test_dashboard_overwrite_requires_version_but_initial_creation_does_not(
    db_session: Session,
) -> None:
    _seed_org(db_session)
    service = DecisionsService(db_session, task_state=FakeTaskStatePort())
    initial = service.handle(
        _propose(
            command_id="00000000-0000-0000-0000-000000000201",
            persona="joe",
            actor=302,
            value="apples",
        ),
        context=_context(event_id="evt-version-initial", hour=9),
    )
    overwrite = _propose(
        command_id="00000000-0000-0000-0000-000000000202",
        persona="joe",
        actor=302,
        value="peaches",
    )

    blocked = service.handle(
        overwrite,
        context=_context(event_id="evt-version-missing", hour=10),
    )
    retried = service.handle(
        overwrite,
        context=_context(event_id="evt-version-missing-retry", hour=11),
    )

    assert initial["status"] == "effective"
    assert blocked == {
        "ok": False,
        "status": "expected_version_required",
        "http_status": 409,
        "current_version": initial["version"],
        "diff": {"v1|task:501|attr:fruit": initial["decision_id"]},
    }
    assert retried == blocked
    assert db_session.scalar(select(func.count()).select_from(Decision)) == 1
    assert db_session.scalar(select(func.count()).select_from(DomainEvent)) == 1
    assert db_session.scalar(select(func.count()).select_from(ProcessedCommand)) == 2


def test_dashboard_task_status_write_requires_current_task_version(
    db_session: Session,
) -> None:
    _seed_org(db_session)
    service = DecisionsService(db_session, task_state=FakeTaskStatePort())
    command = RecordTaskUpdate(
        client_command_id=UUID("00000000-0000-0000-0000-000000000203"),
        persona="jack",
        created_from=CreatedFrom.DASHBOARD,
        task_id=501,
        actor_user_id=304,
        update_kind="status",
        payload={"status": "doing"},
    )

    blocked = service.handle(
        command,
        context=_context(event_id="evt-task-version-missing", hour=9),
    )

    assert blocked == {
        "ok": False,
        "status": "expected_version_required",
        "http_status": 409,
        "current_version": "task-v1",
        "diff": {"task:501": "task-v1"},
    }
    assert db_session.scalar(select(func.count()).select_from(DomainEvent)) == 0


def test_dashboard_approval_requires_the_version_captured_with_the_proposal(
    db_session: Session,
) -> None:
    _seed_org(db_session)
    service = DecisionsService(db_session, task_state=FakeTaskStatePort())
    pending = service.handle(
        _propose(
            command_id="00000000-0000-0000-0000-000000000228",
            persona="jack",
            actor=304,
            value="member-proposal",
        ),
        context=_context(event_id="evt-approval-version-proposal", hour=9),
    )
    approval = ApproveProposal(
        client_command_id=UUID("00000000-0000-0000-0000-000000000229"),
        persona="joe",
        created_from=CreatedFrom.DASHBOARD,
        decision_id=pending["decision_id"],
        approved_by_user_id=302,
    )

    blocked = service.handle(
        approval,
        context=_context(event_id="evt-approval-version-missing", hour=10),
    )

    assert blocked == {
        "ok": False,
        "status": "expected_version_required",
        "http_status": 409,
        "current_version": pending["version"],
        "diff": {},
    }
    assert db_session.get(Decision, pending["decision_id"]).status is DecisionStatus.PROPOSED


def test_concurrent_same_command_id_returns_one_receipt_and_one_event(
    db_session: Session,
) -> None:
    engine = create_engine(os.environ["DATABASE_URL"], pool_pre_ping=True)
    command_id = "00000000-0000-0000-0000-000000000204"
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO users
                    (id, name, handle, role_rank, manager_id, status, departed_at)
                VALUES
                    (9901, 'Concurrent User', 'concurrent-user', 1, NULL, 'ACTIVE', NULL)
                """
            )
        )

    barrier = Barrier(2)

    def submit() -> dict:
        with Session(engine) as session:
            command = RecordSignal(
                client_command_id=UUID(command_id),
                persona="concurrent-user",
                created_from=CreatedFrom.DASHBOARD,
                source_message_id=9901,
                signal_kind="blocker",
                project_id=9901,
                normalized_topic="same click",
                excerpt="same click",
            )
            barrier.wait()
            return DecisionsService(session).handle(
                command,
                context=_context(event_id="evt-concurrent-command", hour=9),
            )

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(executor.map(lambda _index: submit(), range(2)))
        with Session(engine) as check:
            event_count = check.scalar(
                select(func.count())
                .select_from(DomainEvent)
                .where(DomainEvent.caused_by_command == command_id)
            )
            receipt_count = check.scalar(
                select(func.count())
                .select_from(ProcessedCommand)
                .where(ProcessedCommand.client_command_id == command_id)
            )
        assert outcomes[0] == outcomes[1]
        assert outcomes[0]["status"] == "recorded"
        assert event_count == 1
        assert receipt_count == 1
    finally:
        with engine.begin() as connection:
            connection.execute(
                text("DELETE FROM domain_events WHERE caused_by_command = :command_id"),
                {"command_id": command_id},
            )
            connection.execute(
                text("DELETE FROM processed_commands WHERE client_command_id = :command_id"),
                {"command_id": command_id},
            )
            connection.execute(text("DELETE FROM users WHERE id = 9901"))
        engine.dispose()


def test_parallel_non_dashboard_approvals_reload_lifecycle_after_target_lock(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = create_engine(os.environ["DATABASE_URL"], pool_pre_ping=True)
    project_id = 9910
    team_id = 9911
    lead_id = 9912
    task_id = 9913
    source_message_id = 9915
    proposal_command_id = "00000000-0000-0000-0000-000000000230"
    approval_command_ids = (
        "00000000-0000-0000-0000-000000000231",
        "00000000-0000-0000-0000-000000000232",
    )

    class ConcurrentTaskPort:
        task = TaskStateView(
            id=task_id,
            project_id=project_id,
            status=TaskStatus.TODO,
            pic_user_ids=frozenset(),
            owning_team_ids=frozenset({team_id}),
            merged_into=None,
            current_version="task-v1",
        )

        def get_task(self, requested_task_id: int) -> TaskStateView | None:
            return self.task if requested_task_id == task_id else None

    try:
        with Session(engine) as setup:
            setup.add(
                Project(
                    id=project_id,
                    name="Concurrent approval project",
                    kind=ProjectKind.CAMPAIGN,
                    end_date=None,
                    status=ProjectStatus.ACTIVE,
                )
            )
            setup.add(
                Team(
                    id=team_id,
                    project_id=project_id,
                    name="Concurrent approval team",
                )
            )
            setup.add(
                User(
                    id=lead_id,
                    name="Concurrent lead",
                    handle="concurrent-lead",
                    role_rank=2,
                    manager_id=None,
                    status=UserStatus.ACTIVE,
                    departed_at=None,
                )
            )
            setup.add(
                UserTeam(
                    user_id=lead_id,
                    team_id=team_id,
                    role_in_team="lead",
                )
            )
            setup.commit()
            pending = DecisionsService(
                setup,
                task_state=ConcurrentTaskPort(),
            ).handle(
                ProposeDecision(
                    client_command_id=UUID(proposal_command_id),
                    persona="concurrent-lead",
                    created_from=CreatedFrom.LLM,
                    source_message_id=source_message_id,
                    window_id=9916,
                    confidence=0.6,
                    decided_by_user_id=lead_id,
                    scope=DecisionScope.TASK,
                    scope_target=f"task:{task_id}",
                    description="Approval race",
                    ops=[
                        OpSpec(
                            target=f"task:{task_id}",
                            facet="description",
                            op="set",
                            value="approved once",
                        )
                    ],
                    citations=[
                        CitationSpec(
                            message_id=source_message_id,
                            kind=CitationKind.EVIDENCE,
                            rev_at_capture=1,
                        )
                    ],
                ),
                context=_context(
                    event_id="evt-concurrent-proposal",
                    hour=9,
                    citation_authors={source_message_id: lead_id},
                ),
            )
        assert pending["status"] == "proposed"

        target_barrier = Barrier(2)
        original_serialize_targets = gateway_module.serialize_targets

        def synchronize_before_target_lock(session: Session, targets: set[str]) -> None:
            if targets == {f"task:{task_id}"}:
                target_barrier.wait()
            original_serialize_targets(session, targets)

        monkeypatch.setattr(
            gateway_module,
            "serialize_targets",
            synchronize_before_target_lock,
        )

        def approve(index: int) -> dict:
            with Session(engine) as session:
                return DecisionsService(
                    session,
                    task_state=ConcurrentTaskPort(),
                ).handle(
                    ApproveProposal(
                        client_command_id=UUID(approval_command_ids[index]),
                        persona="concurrent-lead",
                        created_from=CreatedFrom.MARKER,
                        source_message_id=9917 + index,
                        decision_id=pending["decision_id"],
                        approved_by_user_id=lead_id,
                    ),
                    context=_context(
                        event_id=f"evt-concurrent-approval-{index}",
                        hour=10 + index,
                    ),
                )

        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(executor.map(approve, range(2)))

        with Session(engine) as check:
            effective_events = check.scalar(
                select(func.count())
                .select_from(DomainEvent)
                .where(
                    DomainEvent.aggregate_id == pending["decision_id"],
                    DomainEvent.kind == "decision_effective",
                )
            )
            self_displacements = check.scalar(
                select(func.count())
                .select_from(DomainEvent)
                .where(
                    DomainEvent.aggregate_id == pending["decision_id"],
                    DomainEvent.kind == "decision_superseded",
                )
            )
            receipt_count = check.scalar(
                select(func.count())
                .select_from(ProcessedCommand)
                .where(
                    ProcessedCommand.client_command_id.in_(
                        (proposal_command_id, *approval_command_ids)
                    )
                )
            )
        assert sorted(outcome["status"] for outcome in outcomes) == ["conflict", "effective"]
        assert effective_events == 1
        assert self_displacements == 0
        assert receipt_count == 3
    finally:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "DELETE FROM effective_units WHERE decision_id IN "
                    "(SELECT id FROM decisions WHERE stable_event_id = "
                    "'evt-concurrent-proposal')"
                )
            )
            connection.execute(
                text(
                    "DELETE FROM decision_citations WHERE decision_id IN "
                    "(SELECT id FROM decisions WHERE stable_event_id = "
                    "'evt-concurrent-proposal')"
                )
            )
            connection.execute(
                text(
                    "DELETE FROM decision_tasks WHERE decision_id IN "
                    "(SELECT id FROM decisions WHERE stable_event_id = "
                    "'evt-concurrent-proposal')"
                )
            )
            connection.execute(
                text(
                    "DELETE FROM domain_events "
                    "WHERE caused_by_command = :proposal_command_id "
                    "OR caused_by_command = :approval_command_id_1 "
                    "OR caused_by_command = :approval_command_id_2"
                ),
                {
                    "proposal_command_id": proposal_command_id,
                    "approval_command_id_1": approval_command_ids[0],
                    "approval_command_id_2": approval_command_ids[1],
                },
            )
            connection.execute(
                text(
                    "DELETE FROM processed_commands "
                    "WHERE client_command_id = :proposal_command_id "
                    "OR client_command_id = :approval_command_id_1 "
                    "OR client_command_id = :approval_command_id_2"
                ),
                {
                    "proposal_command_id": proposal_command_id,
                    "approval_command_id_1": approval_command_ids[0],
                    "approval_command_id_2": approval_command_ids[1],
                },
            )
            connection.execute(
                text(
                    "DELETE FROM decisions "
                    "WHERE stable_event_id = 'evt-concurrent-proposal'"
                )
            )
            connection.execute(
                text("DELETE FROM user_teams WHERE user_id = :user_id"),
                {"user_id": lead_id},
            )
            connection.execute(
                text("DELETE FROM users WHERE id = :user_id"),
                {"user_id": lead_id},
            )
            connection.execute(
                text("DELETE FROM teams WHERE id = :team_id"),
                {"team_id": team_id},
            )
            connection.execute(
                text("DELETE FROM projects WHERE id = :project_id"),
                {"project_id": project_id},
            )
        engine.dispose()


def test_departed_users_have_zero_rank_lead_and_manager_authority(
    db_session: Session,
) -> None:
    _seed_org(db_session)
    joe = db_session.get(User, 302)
    assert joe is not None
    joe.status = UserStatus.DEPARTED
    db_session.flush()
    org = OrgService(db_session)
    service = DecisionsService(db_session, task_state=FakeTaskStatePort())

    assert org.rank_of(302) == 0
    assert org.manager_chain(302) == []
    assert org.manager_chain(304) == [301]
    assert org.lead_user_ids_for_team(201) == set()
    assert org.lead_user_ids_for_project(101) == set()
    assert service.can_decide(302, "v1|task:501|description") is False

    an = db_session.get(User, 301)
    assert an is not None
    an.status = UserStatus.DEPARTED
    db_session.flush()
    assert org.coordinator_user_ids() == set()
    assert service.can_decide(301, "v1|project:101|description") is False

    jack = db_session.get(User, 304)
    assert jack is not None
    jack.status = UserStatus.DEPARTED
    db_session.flush()
    departed_pic = service.handle(
        RecordTaskUpdate(
            client_command_id=UUID("00000000-0000-0000-0000-000000000221"),
            persona="jack",
            created_from=CreatedFrom.MARKER,
            source_message_id=9902,
            task_id=501,
            actor_user_id=304,
            update_kind="status",
            payload={"status": "done"},
        ),
        context=_context(event_id="evt-departed-pic", hour=9),
    )
    assert departed_pic["status"] == "forbidden"
    assert departed_pic["applied"] is False
    assert db_session.scalar(select(func.count()).select_from(DomainEvent)) == 0


def test_departed_maker_cannot_withdraw_or_reject_own_proposal(
    db_session: Session,
) -> None:
    _seed_org(db_session)
    service = DecisionsService(db_session, task_state=FakeTaskStatePort())
    pending = service.handle(
        _propose(
            command_id="00000000-0000-0000-0000-000000000233",
            persona="jack",
            actor=304,
            value="departed-maker",
        ),
        context=_context(event_id="evt-departed-maker-proposal", hour=9),
    )
    maker = db_session.get(User, 304)
    assert maker is not None
    maker.status = UserStatus.DEPARTED
    db_session.flush()

    rejected = service.handle(
        RejectProposal(
            client_command_id=UUID("00000000-0000-0000-0000-000000000234"),
            persona="jack",
            expected_version=pending["version"],
            created_from=CreatedFrom.DASHBOARD,
            decision_id=pending["decision_id"],
            rejected_by_user_id=304,
            reason="veto",
        ),
        context=_context(event_id="evt-departed-maker-reject", hour=10),
    )

    assert rejected["status"] == "challenge_required"
    assert rejected["applied"] is False
    assert db_session.get(Decision, pending["decision_id"]).status is DecisionStatus.PROPOSED


class _TerminalTaskPort:
    def __init__(self) -> None:
        base = {
            "project_id": 101,
            "pic_user_ids": frozenset({304}),
            "owning_team_ids": frozenset({201}),
            "current_version": "task-v2",
        }
        self.tasks = {
            502: TaskStateView(
                id=502,
                status=TaskStatus.CANCELED,
                merged_into=None,
                **base,
            ),
            503: TaskStateView(
                id=503,
                status=TaskStatus.MERGED,
                merged_into=501,
                **base,
            ),
        }

    def get_task(self, task_id: int) -> TaskStateView | None:
        return self.tasks.get(task_id)


def _task_target_proposal(command_id: str, task_id: int) -> ProposeDecision:
    return ProposeDecision(
        client_command_id=UUID(command_id),
        persona="joe",
        created_from=CreatedFrom.DASHBOARD,
        decided_by_user_id=302,
        scope=DecisionScope.TASK,
        scope_target=f"task:{task_id}",
        description="Unsafe direct write",
        ops=[OpSpec(target=f"task:{task_id}", facet="description", op="set", value="new")],
        citations=[],
    )


def test_authorized_direct_proposals_fail_closed_for_missing_canceled_and_merged_tasks(
    db_session: Session,
) -> None:
    _seed_org(db_session)
    service = DecisionsService(db_session, task_state=_TerminalTaskPort())

    missing = service.handle(
        _task_target_proposal(
            "00000000-0000-0000-0000-000000000205",
            599,
        ),
        context=_context(event_id="evt-target-missing", hour=9),
    )
    canceled = service.handle(
        _task_target_proposal(
            "00000000-0000-0000-0000-000000000206",
            502,
        ),
        context=_context(event_id="evt-target-canceled", hour=10),
    )
    merged = service.handle(
        _task_target_proposal(
            "00000000-0000-0000-0000-000000000207",
            503,
        ),
        context=_context(event_id="evt-target-merged", hour=11),
    )

    assert missing["status"] == "revalidation_required"
    assert missing["reason"] == "target_missing"
    assert canceled["status"] == "revalidation_required"
    assert canceled["reason"] == "terminal:canceled"
    assert merged["status"] == "redirect_required"
    assert merged["merged_survivor"] == 501
    assert db_session.scalar(select(func.count()).select_from(Decision)) == 0
    assert db_session.scalar(select(func.count()).select_from(DomainEvent)) == 0


def _multiop_proposal(
    command_id: str,
    *,
    ops: list[OpSpec],
    expected_version: str | None = None,
) -> ProposeDecision:
    return ProposeDecision(
        client_command_id=UUID(command_id),
        persona="joe",
        expected_version=expected_version,
        created_from=CreatedFrom.DASHBOARD,
        decided_by_user_id=302,
        scope=DecisionScope.TASK,
        scope_target="task:501",
        description="Multi-unit replacement",
        ops=ops,
        citations=[],
    )


def test_partial_multiop_supersession_preserves_unaffected_unit_and_restores_displacement(
    db_session: Session,
) -> None:
    _seed_org(db_session)
    service = DecisionsService(db_session, task_state=FakeTaskStatePort())
    fruit_key = "v1|task:501|attr:fruit"
    budget_key = "v1|task:501|attr:budget"
    original = service.handle(
        _multiop_proposal(
            "00000000-0000-0000-0000-000000000208",
            ops=[
                OpSpec(target="task:501", facet="attr:fruit", op="set", value="apple"),
                OpSpec(target="task:501", facet="attr:budget", op="set", value=300),
            ],
        ),
        context=_context(event_id="evt-partial-original", hour=9),
    )
    replacement = service.handle(
        _multiop_proposal(
            "00000000-0000-0000-0000-000000000209",
            expected_version=version_for_bindings({fruit_key: original["decision_id"]}),
            ops=[OpSpec(target="task:501", facet="attr:fruit", op="set", value="peach")],
        ),
        context=_context(event_id="evt-partial-replacement", hour=10),
    )

    original_row = db_session.get(Decision, original["decision_id"])
    assert replacement["status"] == "effective"
    assert original_row is not None
    assert original_row.status is DecisionStatus.EFFECTIVE
    assert db_session.get(EffectiveUnit, fruit_key).decision_id == replacement["decision_id"]
    assert db_session.get(EffectiveUnit, budget_key).decision_id == original["decision_id"]
    effective_event = db_session.scalar(
        select(DomainEvent)
        .where(
            DomainEvent.kind == "decision_effective",
            DomainEvent.aggregate_id == replacement["decision_id"],
        )
        .order_by(DomainEvent.seq.desc())
    )
    assert effective_event.payload["displaced_units"] == [
        {"unit_key": fruit_key, "decision_id": original["decision_id"]}
    ]

    rejected = service.handle(
        RejectProposal(
            client_command_id=UUID("00000000-0000-0000-0000-000000000210"),
            persona="joe",
            expected_version=replacement["version"],
            created_from=CreatedFrom.DASHBOARD,
            decision_id=replacement["decision_id"],
            rejected_by_user_id=302,
            reason="veto",
        ),
        context=_context(event_id="evt-partial-reject", hour=11),
    )
    assert rejected["resurrected_decision_ids"] == [original["decision_id"]]
    assert db_session.get(EffectiveUnit, fruit_key).decision_id == original["decision_id"]
    assert db_session.get(EffectiveUnit, budget_key).decision_id == original["decision_id"]
    assert original_row.status is DecisionStatus.EFFECTIVE


def test_rejecting_multiop_superseder_restores_multiple_predecessors(
    db_session: Session,
) -> None:
    _seed_org(db_session)
    service = DecisionsService(db_session, task_state=FakeTaskStatePort())
    fruit_key = "v1|task:501|attr:fruit"
    budget_key = "v1|task:501|attr:budget"
    fruit = service.handle(
        _multiop_proposal(
            "00000000-0000-0000-0000-000000000211",
            ops=[OpSpec(target="task:501", facet="attr:fruit", op="set", value="apple")],
        ),
        context=_context(event_id="evt-multi-predecessor-fruit", hour=9),
    )
    budget = service.handle(
        _multiop_proposal(
            "00000000-0000-0000-0000-000000000212",
            ops=[OpSpec(target="task:501", facet="attr:budget", op="set", value=300)],
        ),
        context=_context(event_id="evt-multi-predecessor-budget", hour=10),
    )
    superseder = service.handle(
        _multiop_proposal(
            "00000000-0000-0000-0000-000000000213",
            expected_version=version_for_bindings(
                {
                    fruit_key: fruit["decision_id"],
                    budget_key: budget["decision_id"],
                }
            ),
            ops=[
                OpSpec(target="task:501", facet="attr:fruit", op="set", value="peach"),
                OpSpec(target="task:501", facet="attr:budget", op="set", value=500),
            ],
        ),
        context=_context(event_id="evt-multi-superseder", hour=11),
    )

    rejected = service.handle(
        RejectProposal(
            client_command_id=UUID("00000000-0000-0000-0000-000000000214"),
            persona="joe",
            expected_version=superseder["version"],
            created_from=CreatedFrom.DASHBOARD,
            decision_id=superseder["decision_id"],
            rejected_by_user_id=302,
            reason="veto",
        ),
        context=_context(event_id="evt-multi-superseder-reject", hour=12),
    )

    assert rejected["resurrected_decision_ids"] == sorted(
        [fruit["decision_id"], budget["decision_id"]]
    )
    assert db_session.get(EffectiveUnit, fruit_key).decision_id == fruit["decision_id"]
    assert db_session.get(EffectiveUnit, budget_key).decision_id == budget["decision_id"]


def test_resurrection_chain_reuses_original_partial_displacement_evidence(
    db_session: Session,
) -> None:
    _seed_org(db_session)
    service = DecisionsService(db_session, task_state=FakeTaskStatePort())
    fruit_key = "v1|task:501|attr:fruit"
    budget_key = "v1|task:501|attr:budget"
    original = service.handle(
        _multiop_proposal(
            "00000000-0000-0000-0000-000000000235",
            ops=[
                OpSpec(target="task:501", facet="attr:fruit", op="set", value="apple"),
                OpSpec(target="task:501", facet="attr:budget", op="set", value=300),
            ],
        ),
        context=_context(event_id="evt-chain-original", hour=9),
    )
    middle = service.handle(
        _multiop_proposal(
            "00000000-0000-0000-0000-000000000236",
            expected_version=version_for_bindings({fruit_key: original["decision_id"]}),
            ops=[OpSpec(target="task:501", facet="attr:fruit", op="set", value="peach")],
        ),
        context=_context(event_id="evt-chain-middle", hour=10),
    )
    latest = service.handle(
        _multiop_proposal(
            "00000000-0000-0000-0000-000000000237",
            expected_version=middle["version"],
            ops=[OpSpec(target="task:501", facet="attr:fruit", op="set", value="pear")],
        ),
        context=_context(event_id="evt-chain-latest", hour=11),
    )
    restored_middle = service.handle(
        RejectProposal(
            client_command_id=UUID("00000000-0000-0000-0000-000000000238"),
            persona="joe",
            expected_version=latest["version"],
            created_from=CreatedFrom.DASHBOARD,
            decision_id=latest["decision_id"],
            rejected_by_user_id=302,
            reason="veto",
        ),
        context=_context(event_id="evt-chain-reject-latest", hour=12),
    )
    restored_original = service.handle(
        RejectProposal(
            client_command_id=UUID("00000000-0000-0000-0000-000000000239"),
            persona="joe",
            expected_version=restored_middle["version"],
            created_from=CreatedFrom.DASHBOARD,
            decision_id=middle["decision_id"],
            rejected_by_user_id=302,
            reason="veto",
        ),
        context=_context(event_id="evt-chain-reject-middle", hour=13),
    )

    assert restored_middle["resurrected_decision_ids"] == [middle["decision_id"]]
    assert restored_original["resurrected_decision_ids"] == [original["decision_id"]]
    assert db_session.get(EffectiveUnit, fruit_key).decision_id == original["decision_id"]
    assert db_session.get(EffectiveUnit, budget_key).decision_id == original["decision_id"]
    assert db_session.get(Decision, original["decision_id"]).status is DecisionStatus.EFFECTIVE


class _TransferTaskPort:
    def __init__(self) -> None:
        self.tasks = {
            501: TaskStateView(
                id=501,
                project_id=101,
                status=TaskStatus.TODO,
                pic_user_ids=frozenset({304}),
                owning_team_ids=frozenset({201}),
                merged_into=None,
                current_version="task-v1",
            ),
            502: TaskStateView(
                id=502,
                project_id=101,
                status=TaskStatus.CANCELED,
                pic_user_ids=frozenset(),
                owning_team_ids=frozenset({201}),
                merged_into=None,
                current_version="task-v1",
            ),
        }

    def get_task(self, task_id: int) -> TaskStateView | None:
        return self.tasks.get(task_id)


def _seed_transfer_destination(session: Session) -> None:
    session.add(
        Project(
            id=102,
            name="Destination",
            kind=ProjectKind.PROGRAM,
            end_date=None,
            status=ProjectStatus.ACTIVE,
        )
    )
    session.add(Team(id=202, project_id=102, name="Destination team"))
    session.add(
        User(
            id=305,
            name="Destination lead",
            handle="destination-lead",
            role_rank=2,
            manager_id=301,
            status=UserStatus.ACTIVE,
            departed_at=None,
        )
    )
    session.add(UserTeam(user_id=305, team_id=202, role_in_team="lead"))
    session.flush()


def _transfer_proposal(
    command_id: str,
    *,
    persona: str,
    actor: int,
    task_id: int = 501,
    destination: int = 102,
) -> ProposeDecision:
    return ProposeDecision(
        client_command_id=UUID(command_id),
        persona=persona,
        created_from=CreatedFrom.DASHBOARD,
        decided_by_user_id=actor,
        scope=DecisionScope.TASK,
        scope_target=f"task:{task_id}",
        description="Transfer task",
        ops=[
            OpSpec(
                target=f"task:{task_id}",
                facet="project",
                op="set",
                value=destination,
            )
        ],
        citations=[],
    )


def test_cross_project_transfer_requires_distinct_source_and_destination_leads(
    db_session: Session,
) -> None:
    _seed_org(db_session)
    _seed_transfer_destination(db_session)
    tasks = _TransferTaskPort()
    service = DecisionsService(db_session, task_state=tasks)

    pending = service.handle(
        _transfer_proposal(
            "00000000-0000-0000-0000-000000000215",
            persona="joe",
            actor=302,
        ),
        context=_context(event_id="evt-transfer-source", hour=9),
    )
    same_source = service.handle(
        ApproveProposal(
            client_command_id=UUID("00000000-0000-0000-0000-000000000216"),
            persona="joe",
            expected_version=pending["version"],
            created_from=CreatedFrom.DASHBOARD,
            decision_id=pending["decision_id"],
            approved_by_user_id=302,
        ),
        context=_context(event_id="evt-transfer-same-source", hour=10),
    )
    tasks.tasks[501] = replace(tasks.tasks[501], current_version="task-v2")
    stale_task = service.handle(
        ApproveProposal(
            client_command_id=UUID("00000000-0000-0000-0000-000000000217"),
            persona="destination-lead",
            expected_version=pending["version"],
            created_from=CreatedFrom.DASHBOARD,
            decision_id=pending["decision_id"],
            approved_by_user_id=305,
        ),
        context=_context(event_id="evt-transfer-destination", hour=11),
    )
    tasks.tasks[501] = replace(tasks.tasks[501], current_version="task-v1")
    destination = db_session.get(Project, 102)
    assert destination is not None
    destination.status = ProjectStatus.CLOSED
    db_session.flush()
    closed_destination = service.handle(
        ApproveProposal(
            client_command_id=UUID("00000000-0000-0000-0000-000000000224"),
            persona="destination-lead",
            expected_version=pending["version"],
            created_from=CreatedFrom.DASHBOARD,
            decision_id=pending["decision_id"],
            approved_by_user_id=305,
        ),
        context=_context(event_id="evt-transfer-closed-destination", hour=12),
    )
    destination.status = ProjectStatus.ACTIVE
    db_session.flush()
    approved = service.handle(
        ApproveProposal(
            client_command_id=UUID("00000000-0000-0000-0000-000000000225"),
            persona="destination-lead",
            expected_version=pending["version"],
            created_from=CreatedFrom.DASHBOARD,
            decision_id=pending["decision_id"],
            approved_by_user_id=305,
        ),
        context=_context(event_id="evt-transfer-destination-revalidated", hour=13),
    )

    assert pending["status"] == "proposed"
    assert pending["hold_reason"] == "two_key_transfer"
    assert pending["required_approver_ids"] == [305]
    assert same_source["status"] == "authority_required"
    assert stale_task["status"] == "revalidation_required"
    assert stale_task["reason"] == "task_version_changed"
    assert closed_destination["status"] == "invalid"
    assert "destination project must be active" in closed_destination["error"]
    assert approved["status"] == "effective"


def test_cross_project_transfer_with_ambiguous_dual_side_maker_fails_closed(
    db_session: Session,
) -> None:
    _seed_org(db_session)
    _seed_transfer_destination(db_session)
    db_session.add(
        User(
            id=306,
            name="Dual-side lead",
            handle="dual-side-lead",
            role_rank=2,
            manager_id=301,
            status=UserStatus.ACTIVE,
            departed_at=None,
        )
    )
    db_session.add_all(
        [
            UserTeam(user_id=306, team_id=201, role_in_team="lead"),
            UserTeam(user_id=306, team_id=202, role_in_team="lead"),
        ]
    )
    db_session.flush()
    service = DecisionsService(db_session, task_state=_TransferTaskPort())

    pending = service.handle(
        _transfer_proposal(
            "00000000-0000-0000-0000-000000000222",
            persona="dual-side-lead",
            actor=306,
        ),
        context=_context(event_id="evt-transfer-dual-maker", hour=9),
    )
    lead_approval = service.handle(
        ApproveProposal(
            client_command_id=UUID("00000000-0000-0000-0000-000000000223"),
            persona="destination-lead",
            expected_version=pending["version"],
            created_from=CreatedFrom.DASHBOARD,
            decision_id=pending["decision_id"],
            approved_by_user_id=305,
        ),
        context=_context(event_id="evt-transfer-dual-lead-approval", hour=10),
    )

    assert pending["status"] == "proposed"
    assert pending["hold_reason"] == "two_key_transfer"
    assert pending["required_approver_ids"] == [301]
    assert lead_approval["status"] == "authority_required"


def test_transfer_bundle_with_coordinator_only_op_routes_to_coordinator(
    db_session: Session,
) -> None:
    _seed_org(db_session)
    _seed_transfer_destination(db_session)
    service = DecisionsService(db_session, task_state=_TransferTaskPort())
    bundled = _transfer_proposal(
        "00000000-0000-0000-0000-000000000226",
        persona="joe",
        actor=302,
    ).model_copy(
        update={
            "ops": [
                OpSpec(target="task:501", facet="project", op="set", value=102),
                OpSpec(
                    target="project:102",
                    facet="attr:reporting-policy",
                    op="set",
                    value="weekly",
                ),
            ]
        }
    )

    pending = service.handle(
        bundled,
        context=_context(event_id="evt-transfer-bundle", hour=9),
    )
    destination_lead = service.handle(
        ApproveProposal(
            client_command_id=UUID("00000000-0000-0000-0000-000000000227"),
            persona="destination-lead",
            expected_version=pending["version"],
            created_from=CreatedFrom.DASHBOARD,
            decision_id=pending["decision_id"],
            approved_by_user_id=305,
        ),
        context=_context(event_id="evt-transfer-bundle-destination", hour=10),
    )

    assert pending["status"] == "proposed"
    assert pending["required_approver_ids"] == [301]
    assert destination_lead["status"] == "authority_required"


def test_coordinator_can_transfer_alone_and_invalid_transfer_targets_fail_closed(
    db_session: Session,
) -> None:
    _seed_org(db_session)
    _seed_transfer_destination(db_session)
    tasks = _TransferTaskPort()
    service = DecisionsService(db_session, task_state=tasks)

    missing_destination = service.handle(
        _transfer_proposal(
            "00000000-0000-0000-0000-000000000219",
            persona="joe",
            actor=302,
            destination=999,
        ),
        context=_context(event_id="evt-transfer-missing-destination", hour=10),
    )
    coordinator = service.handle(
        _transfer_proposal(
            "00000000-0000-0000-0000-000000000218",
            persona="an",
            actor=301,
        ),
        context=_context(event_id="evt-transfer-coordinator", hour=9),
    )
    canceled_task = service.handle(
        _transfer_proposal(
            "00000000-0000-0000-0000-000000000220",
            persona="joe",
            actor=302,
            task_id=502,
        ),
        context=_context(event_id="evt-transfer-canceled-task", hour=11),
    )

    assert coordinator["status"] == "effective"
    assert missing_destination["status"] == "invalid"
    assert "destination project" in missing_destination["error"]
    assert canceled_task["status"] == "revalidation_required"
    assert canceled_task["reason"] == "terminal:canceled"
