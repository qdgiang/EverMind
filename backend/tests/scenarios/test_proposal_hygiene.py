from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from evermind.contracts.commands import CitationSpec, OpSpec, ProposeDecision
from evermind.contracts.enums import CitationKind, CreatedFrom, DecisionScope
from evermind.db.eventlog import DomainEvent
from evermind.decisions.models import Decision, DecisionCitation
from evermind.decisions.models import DecisionTask
from evermind.decisions.service import DecisionsService
from evermind.decisions.task_state import TaskStateView
from evermind.contracts.enums import TaskStatus, UserStatus
from evermind.org.models import Team, User, UserTeam
from tests.scenarios.test_lifecycle_basics import FakeTaskStatePort, _context, _seed_org


def _marker(
    *,
    command_id: str,
    persona: str,
    actor: int,
    message_id: int,
    value: str,
) -> ProposeDecision:
    return ProposeDecision(
        client_command_id=UUID(command_id),
        persona=persona,
        created_from=CreatedFrom.MARKER,
        source_message_id=message_id,
        decided_by_user_id=actor,
        scope=DecisionScope.TASK,
        scope_target="task:501",
        description=f"Use {value} chairs",
        ops=[OpSpec(target="task:501", facet="attr:chairs", op="set", value=value)],
        citations=[
            CitationSpec(
                message_id=message_id,
                kind=CitationKind.EVIDENCE,
                rev_at_capture=1,
            )
        ],
    )


def test_identical_pending_proposals_collapse_and_union_citations(db_session: Session) -> None:
    """S28/G49: repeated proposal markers create one question and one tracked record."""
    _seed_org(db_session)
    service = DecisionsService(db_session, task_state=FakeTaskStatePort())
    first = service.handle(
        _marker(
            command_id="00000000-0000-0000-0000-000000000031",
            persona="jack",
            actor=304,
            message_id=8101,
            value="blue",
        ),
        context=_context(
            event_id="evt-proposal-1",
            hour=9,
            citation_authors={8101: 304},
        ),
    )
    duplicate = service.handle(
        _marker(
            command_id="00000000-0000-0000-0000-000000000032",
            persona="jack",
            actor=304,
            message_id=8102,
            value="blue",
        ),
        context=_context(
            event_id="evt-proposal-2",
            hour=10,
            citation_authors={8102: 304},
        ),
    )

    assert first["status"] == "proposed"
    assert duplicate == {
        "ok": True,
        "status": "proposal_merged",
        "decision_id": first["decision_id"],
        "version": first["version"],
    }
    assert db_session.scalar(select(func.count()).select_from(Decision)) == 1
    assert db_session.scalar(select(func.count()).select_from(DecisionCitation)) == 2
    assert service.tracked_message_ids() == {8101, 8102}
    assert list(db_session.scalars(select(DomainEvent.kind).order_by(DomainEvent.seq))) == [
        "decision_proposed",
        "corroboration_appended",
    ]


def test_same_value_candidate_becomes_corroboration_without_moving_attribution(
    db_session: Session,
) -> None:
    """G66: a same-value restatement appends evidence, never a new decision."""
    _seed_org(db_session)
    service = DecisionsService(db_session, task_state=FakeTaskStatePort())
    standing = service.handle(
        _marker(
            command_id="00000000-0000-0000-0000-000000000033",
            persona="joe",
            actor=302,
            message_id=8111,
            value="red",
        ),
        context=_context(
            event_id="evt-standing",
            hour=11,
            citation_authors={8111: 302},
        ),
    )
    standing_row = db_session.get(Decision, standing["decision_id"])
    original_ts = standing_row.ts
    corroborated = service.handle(
        _marker(
            command_id="00000000-0000-0000-0000-000000000034",
            persona="jack",
            actor=304,
            message_id=8112,
            value="red",
        ),
        context=_context(
            event_id="evt-restatement",
            hour=12,
            citation_authors={8112: 304},
        ),
    )

    assert corroborated["status"] == "corroborated"
    assert corroborated["decision_id"] == standing["decision_id"]
    assert db_session.scalar(select(func.count()).select_from(Decision)) == 1
    db_session.refresh(standing_row)
    assert standing_row.decided_by_user_id == 302
    assert standing_row.ts == original_ts
    kinds = list(
        db_session.scalars(
            select(DecisionCitation.kind)
            .where(DecisionCitation.decision_id == standing_row.id)
            .order_by(DecisionCitation.id)
        )
    )
    assert kinds == [CitationKind.EVIDENCE, CitationKind.CORROBORATION]


def test_merge_decision_accepts_a_lead_of_either_task_and_links_both_tasks(
    db_session: Session,
) -> None:
    """DEC-7/G43: merge is one decision on the survivor with both task links preserved."""
    _seed_org(db_session)
    db_session.add(Team(id=202, project_id=101, name="Design"))
    db_session.add(
        User(
            id=306,
            name="Lan",
            handle="lan",
            role_rank=2,
            manager_id=301,
            status=UserStatus.ACTIVE,
            departed_at=None,
        )
    )
    db_session.add(UserTeam(user_id=306, team_id=202, role_in_team="lead"))
    db_session.flush()

    class MergeTaskPort:
        tasks = {
            501: TaskStateView(
                id=501,
                project_id=101,
                status=TaskStatus.TODO,
                pic_user_ids=frozenset(),
                owning_team_ids=frozenset({201}),
                merged_into=None,
                current_version="task-v1",
            ),
            502: TaskStateView(
                id=502,
                project_id=101,
                status=TaskStatus.TODO,
                pic_user_ids=frozenset(),
                owning_team_ids=frozenset({202}),
                merged_into=None,
                current_version="task-v1",
            ),
        }

        def get_task(self, task_id: int):
            return self.tasks.get(task_id)

    service = DecisionsService(db_session, task_state=MergeTaskPort())
    merged = service.handle(
        ProposeDecision(
            client_command_id=UUID("00000000-0000-0000-0000-000000000035"),
            persona="lan",
            created_from=CreatedFrom.DASHBOARD,
            decided_by_user_id=306,
            scope=DecisionScope.TASK,
            scope_target="task:501",
            description="Merge duplicate map tasks",
            ops=[OpSpec(target="task:501", facet="merge", op="set", value="task:502")],
            citations=[],
        ),
        context=_context(event_id="evt-merge", hour=13),
    )

    assert merged["status"] == "effective"
    assert set(
        db_session.scalars(
            select(DecisionTask.task_id).where(DecisionTask.decision_id == merged["decision_id"])
        )
    ) == {501, 502}
