from __future__ import annotations

from importlib import import_module

from sqlalchemy.orm import Session

from evermind.contracts.enums import ProjectKind, ProjectStatus, TaskStatus, UserStatus
from evermind.contracts.commands import ApproveProposal, OpSpec, ProposeDecision
from evermind.contracts.enums import CreatedFrom, DecisionScope, DecisionStatus
from evermind.decisions.service import DecisionsService
from evermind.decisions.models import Decision, EffectiveUnit
from evermind.decisions.task_state import TaskStateView
from tests.scenarios.test_lifecycle_basics import _context
from uuid import UUID
from evermind.org.models import Project, Team, User, UserTeam
from evermind.org.service import OrgService


def _seed_matrix_org(session: Session) -> None:
    session.add(
        Project(
            id=101,
            name="Shared fair",
            kind=ProjectKind.CAMPAIGN,
            end_date=None,
            status=ProjectStatus.ACTIVE,
        )
    )
    session.add_all(
        [
            Team(id=201, project_id=101, name="Events"),
            Team(id=202, project_id=101, name="Education"),
            User(
                id=301,
                name="Linh",
                handle="linh",
                role_rank=3,
                manager_id=None,
                status=UserStatus.ACTIVE,
                departed_at=None,
            ),
            User(
                id=302,
                name="Mai",
                handle="mai",
                role_rank=2,
                manager_id=301,
                status=UserStatus.ACTIVE,
                departed_at=None,
            ),
            User(
                id=303,
                name="Phuong",
                handle="phuong",
                role_rank=2,
                manager_id=301,
                status=UserStatus.ACTIVE,
                departed_at=None,
            ),
            User(
                id=304,
                name="Khoa",
                handle="khoa",
                role_rank=1,
                manager_id=302,
                status=UserStatus.ACTIVE,
                departed_at=None,
            ),
        ]
    )
    session.add_all(
        [
            UserTeam(user_id=301, team_id=201, role_in_team="lead"),
            UserTeam(user_id=302, team_id=202, role_in_team="lead"),
            UserTeam(user_id=303, team_id=201, role_in_team="lead"),
            UserTeam(user_id=304, team_id=201, role_in_team="member"),
            UserTeam(user_id=304, team_id=202, role_in_team="member"),
        ]
    )
    session.flush()


def test_org_read_port_exposes_rank_chain_matrix_and_leads(db_session: Session) -> None:
    """S13/G36: authority reads preserve multi-team membership and the manager chain."""
    _seed_matrix_org(db_session)
    org = OrgService(db_session)

    assert org.rank_of(304) == 1
    assert org.manager_chain(304) == [302, 301]
    assert org.team_ids_for_user(304) == {201, 202}
    assert org.lead_user_ids_for_team(201) == {301, 303}
    assert org.lead_user_ids_for_project(101) == {301, 302, 303}


def test_org_read_port_is_safe_for_missing_users_and_manager_cycles(
    db_session: Session,
) -> None:
    """S13/G37: malformed or rootless org data cannot make authority traversal loop."""
    _seed_matrix_org(db_session)
    db_session.get(User, 301).manager_id = 304  # type: ignore[union-attr]
    db_session.flush()
    org = OrgService(db_session)

    assert org.rank_of(999_999) == 0
    assert org.manager_chain(999_999) == []
    assert org.manager_chain(304) == [302, 301]
    assert org.team_ids_for_user(999_999) == set()
    assert org.lead_user_ids_for_team(999_999) == set()


def test_injected_task_state_port_exposes_all_published_read_concepts() -> None:
    """P1 interface #9: A depends on a structural read port, never B's task module."""
    task_state = import_module("evermind.decisions.task_state")
    task = task_state.TaskStateView(
        id=401,
        project_id=101,
        status=TaskStatus.MERGED,
        pic_user_ids=frozenset({304}),
        owning_team_ids=frozenset({201, 202}),
        merged_into=402,
        current_version="task-v7",
    )

    assert task.is_pic(304) is True
    assert task.is_pic(302) is False
    assert task.terminal is True
    assert task.merged_survivor == 402
    assert task.owning_team_ids == frozenset({201, 202})
    assert task.project_id == 101
    assert task.current_version == "task-v7"


def test_can_decide_is_total_for_task_team_project_and_teamless_units(
    db_session: Session,
) -> None:
    """S7/S13 G26/G37/G48: every supported target has a safe authority answer."""
    task_state = import_module("evermind.decisions.task_state")
    _seed_matrix_org(db_session)

    class FakeTaskStatePort:
        def __init__(self) -> None:
            self.tasks = {
                401: task_state.TaskStateView(
                    id=401,
                    project_id=101,
                    status=TaskStatus.TODO,
                    pic_user_ids=frozenset({304}),
                    owning_team_ids=frozenset({201, 202}),
                    merged_into=None,
                    current_version="task-v1",
                ),
                402: task_state.TaskStateView(
                    id=402,
                    project_id=101,
                    status=TaskStatus.TODO,
                    pic_user_ids=frozenset(),
                    owning_team_ids=frozenset(),
                    merged_into=None,
                    current_version="task-v1",
                ),
            }

        def get_task(self, task_id: int):
            return self.tasks.get(task_id)

    service = DecisionsService(db_session, task_state=FakeTaskStatePort())

    assert service.can_decide(302, "v1|task:401|attr:venue") is True
    assert service.can_decide(303, "v1|task:401|attr:venue") is True
    assert service.can_decide(304, "v1|task:401|attr:venue") is False
    assert service.can_decide(302, "v1|task:402|attr:venue") is True
    assert service.can_decide(303, "v1|team:202|attr:class-schedule") is False
    assert service.can_decide(302, "v1|team:202|attr:class-schedule") is True
    assert service.can_decide(302, "v1|project:101|attr:entry-fee") is False
    assert service.can_decide(301, "v1|project:101|attr:entry-fee") is True
    assert service.can_decide(301, "v1|task:999999|description") is False
    assert service.can_decide(301, "v1|unknown:1|description") is False


def test_rootless_peer_write_holds_until_an_involved_lead_tiebreaks(
    db_session: Session,
) -> None:
    """S13/G37: incomparable peer leads never silently last-write-win."""
    db_session.add(
        Project(
            id=111,
            name="Rootless project",
            kind=ProjectKind.CAMPAIGN,
            end_date=None,
            status=ProjectStatus.ACTIVE,
        )
    )
    db_session.add_all(
        [
            Team(id=211, project_id=111, name="A"),
            Team(id=212, project_id=111, name="B"),
            User(
                id=311,
                name="Lead A",
                handle="lead-a",
                role_rank=2,
                manager_id=None,
                status=UserStatus.ACTIVE,
                departed_at=None,
            ),
            User(
                id=312,
                name="Lead B",
                handle="lead-b",
                role_rank=2,
                manager_id=None,
                status=UserStatus.ACTIVE,
                departed_at=None,
            ),
            UserTeam(user_id=311, team_id=211, role_in_team="lead"),
            UserTeam(user_id=312, team_id=212, role_in_team="lead"),
        ]
    )
    db_session.flush()

    class RootlessTaskPort:
        task = TaskStateView(
            id=411,
            project_id=111,
            status=TaskStatus.TODO,
            pic_user_ids=frozenset(),
            owning_team_ids=frozenset({211, 212}),
            merged_into=None,
            current_version="task-v1",
        )

        def get_task(self, task_id: int):
            return self.task if task_id == 411 else None

    def command(
        command_id: str,
        persona: str,
        actor: int,
        value: int,
        *,
        expected_version: str | None = None,
    ) -> ProposeDecision:
        return ProposeDecision(
            client_command_id=UUID(command_id),
            persona=persona,
            expected_version=expected_version,
            created_from=CreatedFrom.DASHBOARD,
            decided_by_user_id=actor,
            scope=DecisionScope.TASK,
            scope_target="task:411",
            description=f"Duration {value}",
            ops=[OpSpec(target="task:411", facet="attr:duration", op="set", value=value)],
            citations=[],
        )

    service = DecisionsService(db_session, task_state=RootlessTaskPort())
    standing = service.handle(
        command(
            "00000000-0000-0000-0000-000000000061",
            "lead-a",
            311,
            20,
        ),
        context=_context(event_id="evt-peer-a", hour=9),
    )
    held = service.handle(
        command(
            "00000000-0000-0000-0000-000000000062",
            "lead-b",
            312,
            15,
            expected_version=standing["version"],
        ),
        context=_context(event_id="evt-peer-b", hour=10),
    )

    assert held["status"] == "proposed"
    assert held["hold_reason"] == "peer_conflict"
    assert held["required_approver_ids"] == [311, 312]
    assert (
        db_session.get(EffectiveUnit, "v1|task:411|attr:duration").decision_id
        == (standing["decision_id"])
    )

    approved = service.handle(
        ApproveProposal(
            client_command_id=UUID("00000000-0000-0000-0000-000000000063"),
            persona="lead-a",
            expected_version=held["version"],
            created_from=CreatedFrom.DASHBOARD,
            decision_id=held["decision_id"],
            approved_by_user_id=311,
        ),
        context=_context(event_id="evt-peer-tiebreak", hour=11),
    )
    assert approved["status"] == "effective"
    assert db_session.get(Decision, standing["decision_id"]).status is DecisionStatus.SUPERSEDED
