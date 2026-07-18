from __future__ import annotations

from datetime import datetime
from importlib import import_module
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from evermind.contracts.commands import (
    ApproveProposal,
    CitationSpec,
    OpSpec,
    ProposeDecision,
    RejectProposal,
)
from evermind.contracts.enums import (
    ApprovalVia,
    CitationKind,
    CreatedFrom,
    DecisionScope,
    DecisionStatus,
    ProjectKind,
    ProjectStatus,
    TaskStatus,
    UserStatus,
)
from evermind.db.eventlog import DomainEvent
from evermind.decisions.models import Decision, EffectiveUnit, ProcessedCommand
from evermind.decisions.service import DecisionsService
from evermind.decisions.task_state import TaskStateView
from evermind.org.models import Project, Team, User, UserTeam


class FakeTaskStatePort:
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
            )
        }

    def get_task(self, task_id: int) -> TaskStateView | None:
        return self.tasks.get(task_id)


def _seed_org(session: Session) -> None:
    session.add(
        Project(
            id=101,
            name="Year-end gala",
            kind=ProjectKind.CAMPAIGN,
            end_date=None,
            status=ProjectStatus.ACTIVE,
        )
    )
    session.add(Team(id=201, project_id=101, name="IT"))
    session.add_all(
        [
            User(
                id=301,
                name="An",
                handle="an",
                role_rank=3,
                manager_id=None,
                status=UserStatus.ACTIVE,
                departed_at=None,
            ),
            User(
                id=302,
                name="Joe",
                handle="joe",
                role_rank=2,
                manager_id=301,
                status=UserStatus.ACTIVE,
                departed_at=None,
            ),
            User(
                id=304,
                name="Jack",
                handle="jack",
                role_rank=1,
                manager_id=302,
                status=UserStatus.ACTIVE,
                departed_at=None,
            ),
        ]
    )
    session.add_all(
        [
            UserTeam(user_id=302, team_id=201, role_in_team="lead"),
            UserTeam(user_id=304, team_id=201, role_in_team="member"),
        ]
    )
    session.flush()


def _context(
    *,
    event_id: str,
    hour: int,
    citation_authors: dict[int, int] | None = None,
    delegated_by_user_id: int | None = None,
    explicit_supersedes_decision_id: int | None = None,
):
    ordering = import_module("evermind.decisions.ordering")
    return ordering.HandleContext(
        event_ts=datetime(2026, 11, 12, hour, 0),
        recorded_at=datetime(2026, 11, 12, hour, 1),
        stable_event_id=event_id,
        citation_authors=citation_authors or {},
        delegated_by_user_id=delegated_by_user_id,
        explicit_supersedes_decision_id=explicit_supersedes_decision_id,
    )


def _propose(
    *,
    command_id: str,
    persona: str,
    actor: int,
    value: str,
    expected_version: str | None = None,
) -> ProposeDecision:
    return ProposeDecision(
        client_command_id=UUID(command_id),
        persona=persona,
        expected_version=expected_version,
        created_from=CreatedFrom.DASHBOARD,
        decided_by_user_id=actor,
        scope=DecisionScope.TASK,
        scope_target="task:501",
        description=f"Buy {value}",
        ops=[OpSpec(target="task:501", facet="attr:fruit", op="set", value=value)],
        citations=[],
    )


def test_authorized_decision_is_effective_with_unit_event_and_receipt(
    db_session: Session,
) -> None:
    """S1/DEC-1..4: an authorized human command effects atomically."""
    _seed_org(db_session)
    service = DecisionsService(db_session, task_state=FakeTaskStatePort())
    command = _propose(
        command_id="00000000-0000-0000-0000-000000000001",
        persona="joe",
        actor=302,
        value="apples",
    )

    outcome = service.handle(command, context=_context(event_id="evt-1", hour=9))

    decision = db_session.scalar(select(Decision))
    event = db_session.scalar(select(DomainEvent))
    receipt = db_session.scalar(select(ProcessedCommand))
    unit = db_session.scalar(select(EffectiveUnit))
    assert outcome == {
        "ok": True,
        "status": "effective",
        "decision_id": decision.id,
        "version": outcome["version"],
    }
    assert outcome["version"].startswith("v1:")
    assert decision.status is DecisionStatus.EFFECTIVE
    assert decision.decided_by_role_at_time == 2
    assert decision.confidence == 1.0
    assert decision.stable_event_id == "evt-1"
    assert unit.decision_id == decision.id
    assert event.kind == "decision_effective"
    assert event.caused_by_command == str(command.client_command_id)
    assert receipt.outcome == outcome


def test_s3_apple_to_peach_respects_rank_gate_then_sweeps_proposals(
    db_session: Session,
) -> None:
    """S3/G10-G12: lower-rank replacement waits; approval flips and sweeps atomically."""
    _seed_org(db_session)
    service = DecisionsService(db_session, task_state=FakeTaskStatePort())
    apple = service.handle(
        _propose(
            command_id="00000000-0000-0000-0000-000000000011",
            persona="an",
            actor=301,
            value="apples",
        ),
        context=_context(event_id="evt-apple", hour=9),
    )
    green_apple = service.handle(
        _propose(
            command_id="00000000-0000-0000-0000-000000000012",
            persona="jack",
            actor=304,
            value="green-apples",
            expected_version=apple["version"],
        ),
        context=_context(event_id="evt-green", hour=10),
    )
    peach = service.handle(
        _propose(
            command_id="00000000-0000-0000-0000-000000000013",
            persona="joe",
            actor=302,
            value="peaches",
            expected_version=apple["version"],
        ),
        context=_context(event_id="evt-peach", hour=14),
    )

    assert apple["status"] == "effective"
    assert green_apple["status"] == "proposed"
    assert peach["status"] == "proposed"

    approved = service.handle(
        ApproveProposal(
            client_command_id=UUID("00000000-0000-0000-0000-000000000014"),
            persona="an",
            expected_version=peach["version"],
            created_from=CreatedFrom.DASHBOARD,
            decision_id=peach["decision_id"],
            approved_by_user_id=301,
        ),
        context=_context(event_id="evt-approve", hour=15),
    )

    apple_row = db_session.get(Decision, apple["decision_id"])
    green_row = db_session.get(Decision, green_apple["decision_id"])
    peach_row = db_session.get(Decision, peach["decision_id"])
    unit = db_session.scalar(select(EffectiveUnit))
    event_kinds = list(db_session.scalars(select(DomainEvent.kind).order_by(DomainEvent.seq)))
    assert approved["status"] == "effective"
    assert apple_row.status is DecisionStatus.SUPERSEDED
    assert apple_row.superseded_by_decision_id == peach_row.id
    assert green_row.status is DecisionStatus.REJECTED
    assert green_row.rejected_reason.value == "overruled"
    assert green_row.superseded_by_decision_id == peach_row.id
    assert peach_row.status is DecisionStatus.EFFECTIVE
    assert peach_row.supersedes_decision_id == apple_row.id
    assert peach_row.approved_by_user_id == 301
    assert peach_row.approval_via is ApprovalVia.AUTHORITY
    assert peach_row.approved_by_role_at_act == 3
    assert unit.decision_id == peach_row.id
    assert event_kinds == [
        "decision_effective",
        "decision_proposed",
        "decision_proposed",
        "decision_superseded",
        "decision_rejected",
        "decision_effective",
    ]


def test_confidence_relay_self_confirm_and_delegation_gates(db_session: Session) -> None:
    """S5/S18 G18-G19: evidence, confidence, relay, and delegation gates are explicit."""
    _seed_org(db_session)
    service = DecisionsService(db_session, task_state=FakeTaskStatePort())
    low_confidence = ProposeDecision(
        client_command_id=UUID("00000000-0000-0000-0000-000000000021"),
        persona="joe",
        created_from=CreatedFrom.LLM,
        source_message_id=8001,
        window_id=7001,
        confidence=0.6,
        decided_by_user_id=302,
        scope=DecisionScope.TASK,
        scope_target="task:501",
        description="Raise budget",
        ops=[OpSpec(target="task:501", facet="attr:budget", op="set", value=1000)],
        citations=[
            CitationSpec(
                message_id=8001,
                kind=CitationKind.EVIDENCE,
                rev_at_capture=1,
            )
        ],
    )
    low_outcome = service.handle(
        low_confidence,
        context=_context(
            event_id="evt-low",
            hour=9,
            citation_authors={8001: 302},
        ),
    )
    assert low_outcome["status"] == "proposed"

    confirmed = service.handle(
        ApproveProposal(
            client_command_id=UUID("00000000-0000-0000-0000-000000000022"),
            persona="joe",
            expected_version=low_outcome["version"],
            created_from=CreatedFrom.DASHBOARD,
            decision_id=low_outcome["decision_id"],
            approved_by_user_id=302,
        ),
        context=_context(event_id="evt-self-confirm", hour=10),
    )
    confirmed_row = db_session.get(Decision, confirmed["decision_id"])
    assert confirmed["status"] == "effective"
    assert confirmed_row.approval_via is ApprovalVia.SELF_CONFIRM

    relayed = service.handle(
        ProposeDecision(
            client_command_id=UUID("00000000-0000-0000-0000-000000000023"),
            persona="joe",
            created_from=CreatedFrom.LLM,
            source_message_id=8002,
            window_id=7002,
            confidence=0.99,
            decided_by_user_id=302,
            scope=DecisionScope.TASK,
            scope_target="task:501",
            description="Move the date on Mai's behalf",
            ops=[OpSpec(target="task:501", facet="end_date", op="set", value="2026-12-01")],
            citations=[
                CitationSpec(
                    message_id=8002,
                    kind=CitationKind.EVIDENCE,
                    rev_at_capture=1,
                )
            ],
        ),
        context=_context(
            event_id="evt-relay",
            hour=11,
            citation_authors={8002: 304},
        ),
    )
    assert relayed["status"] == "proposed"

    delegated = service.handle(
        ProposeDecision(
            client_command_id=UUID("00000000-0000-0000-0000-000000000024"),
            persona="jack",
            created_from=CreatedFrom.LLM,
            source_message_id=8003,
            window_id=7003,
            confidence=0.99,
            decided_by_user_id=304,
            scope=DecisionScope.TASK,
            scope_target="task:501",
            description="Joe delegated the purchase choice",
            ops=[OpSpec(target="task:501", facet="attr:vendor", op="set", value="A")],
            citations=[
                CitationSpec(
                    message_id=8003,
                    kind=CitationKind.EVIDENCE,
                    rev_at_capture=1,
                ),
                CitationSpec(
                    message_id=8004,
                    kind=CitationKind.APPROVAL,
                    rev_at_capture=1,
                    rev_at_act=1,
                ),
            ],
        ),
        context=_context(
            event_id="evt-delegated",
            hour=12,
            citation_authors={8003: 304, 8004: 302},
            delegated_by_user_id=302,
        ),
    )
    delegated_row = db_session.get(Decision, delegated["decision_id"])
    assert delegated["status"] == "effective"
    assert delegated_row.decided_by_role_at_time == 1
    assert delegated_row.approval_via is ApprovalVia.DELEGATION
    assert delegated_row.approved_by_user_id == 302
    assert delegated_row.approved_by_role_at_act == 2


def test_rejection_challenge_resurrection_and_withdrawal(db_session: Session) -> None:
    """S5/G17-G18 and #17b: challenge first, maker veto resurrects, proposer withdraws."""
    _seed_org(db_session)
    service = DecisionsService(db_session, task_state=FakeTaskStatePort())
    budget_300 = service.handle(
        _propose(
            command_id="00000000-0000-0000-0000-000000000041",
            persona="joe",
            actor=302,
            value="budget-300",
        ),
        context=_context(event_id="evt-budget-300", hour=9),
    )
    budget_1000 = service.handle(
        _propose(
            command_id="00000000-0000-0000-0000-000000000042",
            persona="joe",
            actor=302,
            value="budget-1000",
            expected_version=budget_300["version"],
        ),
        context=_context(event_id="evt-budget-1000", hour=10),
    )

    challenge = service.handle(
        RejectProposal(
            client_command_id=UUID("00000000-0000-0000-0000-000000000043"),
            persona="jack",
            expected_version=budget_1000["version"],
            created_from=CreatedFrom.DASHBOARD,
            decision_id=budget_1000["decision_id"],
            rejected_by_user_id=304,
            reason="veto",
        ),
        context=_context(event_id="evt-challenge", hour=11),
    )
    assert challenge["status"] == "challenge_required"
    assert challenge["applied"] is False
    assert db_session.get(Decision, budget_1000["decision_id"]).status is DecisionStatus.EFFECTIVE

    rejected = service.handle(
        RejectProposal(
            client_command_id=UUID("00000000-0000-0000-0000-000000000044"),
            persona="joe",
            expected_version=budget_1000["version"],
            created_from=CreatedFrom.DASHBOARD,
            decision_id=budget_1000["decision_id"],
            rejected_by_user_id=302,
            reason="veto",
        ),
        context=_context(event_id="evt-veto", hour=12),
    )
    old_row = db_session.get(Decision, budget_300["decision_id"])
    rejected_row = db_session.get(Decision, budget_1000["decision_id"])
    unit = db_session.scalar(select(EffectiveUnit))
    assert rejected["status"] == "rejected"
    assert rejected_row.status is DecisionStatus.REJECTED
    assert rejected_row.rejected_reason.value == "veto"
    assert old_row.status is DecisionStatus.EFFECTIVE
    assert old_row.superseded_by_decision_id is None
    assert unit.decision_id == old_row.id

    pending = service.handle(
        _propose(
            command_id="00000000-0000-0000-0000-000000000045",
                persona="jack",
                actor=304,
                value="withdraw-me",
                expected_version=rejected["version"],
        ),
        context=_context(event_id="evt-pending-withdraw", hour=13),
    )
    withdrawn = service.handle(
        RejectProposal(
            client_command_id=UUID("00000000-0000-0000-0000-000000000046"),
            persona="jack",
            expected_version=pending["version"],
            created_from=CreatedFrom.DASHBOARD,
            decision_id=pending["decision_id"],
            rejected_by_user_id=304,
            reason="veto",
        ),
        context=_context(event_id="evt-withdraw", hour=14),
    )
    pending_row = db_session.get(Decision, pending["decision_id"])
    assert withdrawn["status"] == "rejected"
    assert pending_row.rejected_reason.value == "withdrawn"
