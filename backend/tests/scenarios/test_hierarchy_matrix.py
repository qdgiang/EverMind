"""L1 — hierarchy & the matrix (S13, S21). Pins: user_teams matrix membership
(G36), rootless fallback (G37), peer-conflict hold (§Facets), delegation (G25)."""
from __future__ import annotations

from evermind.contracts.enums import CreatedFrom, DecisionScope, UserStatus
from evermind.decisions.authority import AuthorityService
from evermind.org.models import Team, User, UserTeam
from evermind.org.service import OrgService


def test_matrix_task_owned_by_two_teams(service, task_port, org_ids, mk):
    """G36: a task owned by two teams (khoa's double hat) is decidable by
    EITHER owning team's lead."""
    mai = org_ids["users"]["mai"]
    ev, ed = org_ids["teams"]["TEAM-EV"], org_ids["teams"]["TEAM-ED"]
    task_port.add(5, org_ids["projects"]["P-TT"], team_ids=[ev, ed])
    outcome = service.handle(mk.propose(mai, [mk.op_set("task:5", "attr:slot", "9:00")]))
    assert outcome["status"] == "effective"  # mai leads ED, one of the owners


def test_member_of_two_teams_still_member(service, task_port, org_ids, mk):
    """G36: matrix membership grants no authority — khoa (EV + ED member)
    still proposes."""
    khoa = org_ids["users"]["khoa"]
    task_port.add(5, org_ids["projects"]["P-TT"],
                  team_ids=[org_ids["teams"]["TEAM-EV"], org_ids["teams"]["TEAM-ED"]])
    outcome = service.handle(mk.propose(
        khoa, [mk.op_set("task:5", "attr:slot", "10:00")],
        created_from=CreatedFrom.LLM, confidence=0.9))
    assert outcome["status"] == "proposed"


def test_peer_conflict_hold(service, task_port, org_ids, org, mk, db_session):
    """§Facets peer conflict: a second same-unit effective write from an
    equal-rank, incomparable peer is held `proposed`, both sides tagged —
    explicit human tiebreak, never silent last-write-wins."""
    mai = org_ids["users"]["mai"]
    # a second lead, peer to mai (both rank 2, both managed by linh)
    phuong = User(name="Phuong", handle="phuong", role_rank=2,
                  manager_id=org_ids["users"]["linh"], status=UserStatus.ACTIVE)
    db_session.add(phuong)
    db_session.flush()
    shared_team = Team(project_id=org_ids["projects"]["P-CL"], name="shared")
    db_session.add(shared_team)
    db_session.flush()
    db_session.add(UserTeam(user_id=mai, team_id=shared_team.id, role_in_team="lead"))
    db_session.flush()
    task_port.add(9, org_ids["projects"]["P-CL"], team_ids=[shared_team.id])

    standing = service.handle(mk.propose(mai, [mk.op_set("task:9", "attr:plan", "A")]))
    assert standing["status"] == "effective"

    # make phuong authorized over the same unit via a second owning team
    phuong_team = Team(project_id=org_ids["projects"]["P-CL"], name="phuong-team")
    db_session.add(phuong_team)
    db_session.flush()
    db_session.add(UserTeam(user_id=phuong.id, team_id=phuong_team.id, role_in_team="lead"))
    db_session.flush()
    task_port.tasks[9].team_ids.append(phuong_team.id)

    contested = service.handle(mk.propose(phuong.id, [mk.op_set("task:9", "attr:plan", "B")]))
    assert contested["status"] == "proposed"
    assert contested["hold_reason"] == "peer_hold"
    assert set(contested["peers"]) == {mai, phuong.id}
    # the standing decision stays effective throughout — an unresolved tie
    # displaces nothing (design-v2 §Facet registry)
    from evermind.decisions.models import Decision
    from evermind.contracts.enums import DecisionStatus
    assert db_session.get(Decision, standing["decision_id"]).status is DecisionStatus.EFFECTIVE


def test_rootless_fallback_apex_is_all_leads(db_session):
    """G37: with no coordinator anywhere, the apex approver set is every lead."""
    lead_a = User(name="A", handle="lead-a", role_rank=2, status=UserStatus.ACTIVE)
    lead_b = User(name="B", handle="lead-b", role_rank=2, status=UserStatus.ACTIVE)
    db_session.add_all([lead_a, lead_b])
    db_session.flush()
    authority = AuthorityService(OrgService(db_session))
    verdict = authority.can_decide_target(lead_a.id, DecisionScope.TASK, "task:1", None)
    assert not verdict.allowed  # nobody outranks anybody silently
    assert set(verdict.approvers) == {lead_a.id, lead_b.id}


def test_delegation_born_effective(service, task_port, org_ids, mk, db_session):
    """G25: "minh chốt luôn nhé" — an authorized user's cited in-thread message
    authorizes the member; the decision is born effective via delegation with
    both messages cited."""
    minh, linh = org_ids["users"]["minh"], org_ids["users"]["linh"]
    task_port.add(1, org_ids["projects"]["P-TT"], team_ids=[org_ids["teams"]["TEAM-EV"]])
    outcome = service.handle(mk.propose(
        minh, [mk.op_set("task:1", "attr:sound", "vendor X")],
        created_from=CreatedFrom.LLM, confidence=0.9,
        delegated_by_user_id=linh, delegation_message_id=54))
    assert outcome["status"] == "effective"
    from evermind.decisions.models import Decision, DecisionCitation
    from sqlalchemy import select
    decision = db_session.get(Decision, outcome["decision_id"])
    assert decision.approval_via.value == "delegation"
    assert decision.decided_by_user_id == minh  # attribution stays with the maker
    cited = set(db_session.scalars(select(DecisionCitation.message_id).where(
        DecisionCitation.decision_id == decision.id)))
    assert 54 in cited  # the delegating message rides along
