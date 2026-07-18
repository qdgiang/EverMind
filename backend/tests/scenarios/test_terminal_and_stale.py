from __future__ import annotations

from dataclasses import replace
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from evermind.contracts.commands import (
    ApproveProposal,
    OpSpec,
    ProposeDecision,
    RecordTaskUpdate,
)
from evermind.contracts.enums import (
    CreatedFrom,
    DecisionScope,
    DecisionStatus,
    TaskStatus,
    UserStatus,
)
from evermind.db.eventlog import DomainEvent
from evermind.decisions.models import Decision, ProcessedCommand
from evermind.decisions.service import DecisionsService
from evermind.decisions.task_state import TaskStateView
from evermind.org.models import User, UserTeam
from tests.scenarios.test_lifecycle_basics import _context, _seed_org


class MutableTaskStatePort:
    def __init__(self) -> None:
        base = dict(
            project_id=101,
            pic_user_ids=frozenset({304}),
            owning_team_ids=frozenset({201}),
            merged_into=None,
            current_version="task-v1",
        )
        self.tasks = {
            501: TaskStateView(id=501, status=TaskStatus.TODO, **base),
            502: TaskStateView(id=502, status=TaskStatus.CANCELED, **base),
            503: TaskStateView(
                id=503,
                status=TaskStatus.MERGED,
                **{**base, "merged_into": 504},
            ),
            504: TaskStateView(id=504, status=TaskStatus.TODO, **base),
        }

    def get_task(self, task_id: int) -> TaskStateView | None:
        return self.tasks.get(task_id)


def _pending_end_date(command_id: str) -> ProposeDecision:
    return ProposeDecision(
        client_command_id=UUID(command_id),
        persona="jack",
        created_from=CreatedFrom.DASHBOARD,
        decided_by_user_id=304,
        scope=DecisionScope.TASK,
        scope_target="task:501",
        description="Extend the worksheet",
        ops=[OpSpec(target="task:501", facet="end_date", op="set", value="2026-11-25")],
        citations=[],
    )


def test_approval_revalidates_terminal_merged_and_task_version_state(
    db_session: Session,
) -> None:
    """S31/G52/EVM-005: approval acts re-read task state and authority at act time."""
    _seed_org(db_session)
    tasks = MutableTaskStatePort()
    service = DecisionsService(db_session, task_state=tasks)
    pending = service.handle(
        _pending_end_date("00000000-0000-0000-0000-000000000091"),
        context=_context(event_id="evt-stale-proposal", hour=9),
    )
    assert pending["task_versions"] == {"501": "task-v1"}
    event_count = db_session.scalar(select(func.count()).select_from(DomainEvent))

    tasks.tasks[501] = replace(
        tasks.tasks[501],
        status=TaskStatus.CANCELED,
        current_version="task-v2",
    )
    blocked = service.handle(
        ApproveProposal(
            client_command_id=UUID("00000000-0000-0000-0000-000000000092"),
            persona="joe",
            expected_version=pending["version"],
            created_from=CreatedFrom.DASHBOARD,
            decision_id=pending["decision_id"],
            approved_by_user_id=302,
        ),
        context=_context(event_id="evt-stale-approval", hour=10),
    )

    assert blocked == {
        "ok": False,
        "status": "revalidation_required",
        "http_status": 409,
        "decision_id": pending["decision_id"],
        "reason": "terminal:canceled",
        "current_task_version": "task-v2",
    }
    assert db_session.get(Decision, pending["decision_id"]).status is DecisionStatus.PROPOSED
    assert db_session.scalar(select(func.count()).select_from(DomainEvent)) == event_count

    tasks.tasks[501] = replace(
        tasks.tasks[501],
        status=TaskStatus.MERGED,
        merged_into=504,
        current_version="task-v3",
    )
    redirect = service.handle(
        ApproveProposal(
            client_command_id=UUID("00000000-0000-0000-0000-000000000098"),
            persona="joe",
            expected_version=pending["version"],
            created_from=CreatedFrom.DASHBOARD,
            decision_id=pending["decision_id"],
            approved_by_user_id=302,
        ),
        context=_context(event_id="evt-merged-approval", hour=11),
    )
    assert redirect["status"] == "redirect_required"
    assert redirect["merged_survivor"] == 504

    tasks.tasks[501] = replace(
        tasks.tasks[501],
        status=TaskStatus.TODO,
        merged_into=None,
        current_version="task-v4",
    )
    version_diff = service.handle(
        ApproveProposal(
            client_command_id=UUID("00000000-0000-0000-0000-000000000099"),
            persona="joe",
            expected_version=pending["version"],
            created_from=CreatedFrom.DASHBOARD,
            decision_id=pending["decision_id"],
            approved_by_user_id=302,
        ),
        context=_context(event_id="evt-version-diff-approval", hour=12),
    )
    assert version_diff["status"] == "revalidation_required"
    assert version_diff["reason"] == "task_version_changed"

    tasks.tasks[501] = replace(tasks.tasks[501], current_version="task-v1")
    joe = db_session.get(User, 302)
    joe.role_rank = 1
    db_session.flush()
    demoted = service.handle(
        ApproveProposal(
            client_command_id=UUID("00000000-0000-0000-0000-000000000100"),
            persona="joe",
            expected_version=pending["version"],
            created_from=CreatedFrom.DASHBOARD,
            decision_id=pending["decision_id"],
            approved_by_user_id=302,
        ),
        context=_context(event_id="evt-demoted-approval", hour=13),
    )
    assert demoted["status"] == "authority_required"
    assert db_session.scalar(select(func.count()).select_from(DomainEvent)) == event_count


def test_task_update_routes_pic_authority_confirmation_terminal_and_merge_without_apply_leaks(
    db_session: Session,
) -> None:
    """S31/G52: task commands route through A while B remains event-only."""
    _seed_org(db_session)
    db_session.add(
        User(
            id=305,
            name="Minh",
            handle="minh",
            role_rank=1,
            manager_id=302,
            status=UserStatus.ACTIVE,
            departed_at=None,
        )
    )
    db_session.add(UserTeam(user_id=305, team_id=201, role_in_team="member"))
    db_session.flush()
    tasks = MutableTaskStatePort()
    service = DecisionsService(db_session, task_state=tasks)

    def update(
        command_id: str,
        *,
        persona: str,
        actor: int,
        task_id: int,
        kind: str = "status",
    ) -> dict:
        return service.handle(
            RecordTaskUpdate(
                client_command_id=UUID(command_id),
                persona=persona,
                created_from=CreatedFrom.MARKER,
                source_message_id=int(command_id[-3:]),
                task_id=task_id,
                actor_user_id=actor,
                update_kind=kind,
                payload={"status": "doing"} if kind == "status" else {"note": "context"},
            ),
            context=_context(event_id=f"evt-{command_id[-3:]}", hour=11),
        )

    pic = update(
        "00000000-0000-0000-0000-000000000093",
        persona="jack",
        actor=304,
        task_id=501,
    )
    unauthorized = update(
        "00000000-0000-0000-0000-000000000094",
        persona="minh",
        actor=305,
        task_id=501,
    )
    terminal = update(
        "00000000-0000-0000-0000-000000000095",
        persona="jack",
        actor=304,
        task_id=502,
    )
    terminal_note = update(
        "00000000-0000-0000-0000-000000000096",
        persona="jack",
        actor=304,
        task_id=502,
        kind="note",
    )
    merged = update(
        "00000000-0000-0000-0000-000000000097",
        persona="jack",
        actor=304,
        task_id=503,
    )

    events = list(db_session.scalars(select(DomainEvent).order_by(DomainEvent.seq)))
    assert pic["status"] == "applied"
    assert pic["lane"] == "pic"
    assert unauthorized["status"] == "confirmation_required"
    assert unauthorized["applied"] is False
    assert terminal["status"] == "terminal_locked"
    assert terminal["applied"] is False
    assert terminal_note["status"] == "applied"
    assert merged["status"] == "applied"
    assert merged["task_id"] == 504
    assert merged["redirected_from"] == 503
    assert [event.aggregate_id for event in events] == [501, 502, 504]
    assert all(event.kind == "task_update_recorded" for event in events)
    assert db_session.scalar(select(func.count()).select_from(ProcessedCommand)) == 5
