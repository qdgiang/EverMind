"""L1 — policies & scopes (S7, S27). Pins: team/project scope (G26), team-less
governance (G48), `can_decide` total (DEC-4)."""
from __future__ import annotations

import uuid

from evermind.contracts.commands import ApproveProposal
from evermind.contracts.enums import CreatedFrom, DecisionScope


def test_team_policy_lead_born_effective(service, org_ids, mk):
    """G26: a team-scoped policy by that team's lead is born effective."""
    mai = org_ids["users"]["mai"]
    ed = org_ids["teams"]["TEAM-ED"]
    outcome = service.handle(mk.propose(
        mai, [mk.op_set(f"team:{ed}", "attr:class-schedule", "Sun 9:00")],
        scope=DecisionScope.TEAM, scope_target=f"team:{ed}"))
    assert outcome["status"] == "effective"


def test_team_policy_member_held(service, org_ids, mk):
    """G26: a member's team policy waits for the lead."""
    tuan = org_ids["users"]["tuan"]
    mai = org_ids["users"]["mai"]
    ed = org_ids["teams"]["TEAM-ED"]
    outcome = service.handle(mk.propose(
        tuan, [mk.op_set(f"team:{ed}", "attr:class-schedule", "Sun 14:00")],
        scope=DecisionScope.TEAM, scope_target=f"team:{ed}",
        created_from=CreatedFrom.LLM, confidence=0.92))
    assert outcome["status"] == "proposed"
    assert mai in outcome["approvers"]


def test_project_policy_needs_coordinator(service, org_ids, mk, db_session):
    """S7: project-scoped policy — a lead proposes, the coordinator's approval
    effects it."""
    mai, linh = org_ids["users"]["mai"], org_ids["users"]["linh"]
    cl = org_ids["projects"]["P-CL"]
    outcome = service.handle(mk.propose(
        mai, [mk.op_set(f"project:{cl}", "attr:budget-cap", "10tr")],
        scope=DecisionScope.PROJECT, scope_target=f"project:{cl}"))
    assert outcome["status"] == "proposed"
    assert linh in outcome["approvers"]

    approved = service.handle(ApproveProposal(
        client_command_id=uuid.uuid4(), persona="user-linh",
        created_from=CreatedFrom.DASHBOARD, decision_id=outcome["decision_id"],
        approved_by_user_id=linh))
    assert approved["status"] == "effective"


def test_project_policy_coordinator_born_effective(service, org_ids, mk):
    linh = org_ids["users"]["linh"]
    tt = org_ids["projects"]["P-TT"]
    outcome = service.handle(mk.propose(
        linh, [mk.op_set(f"project:{tt}", "attr:entry-fee", "free")],
        scope=DecisionScope.PROJECT, scope_target=f"project:{tt}"))
    assert outcome["status"] == "effective"


def test_teamless_task_project_level_governance(service, task_port, org_ids, mk):
    """S27/G48: a team-less task is governed project-level — any lead of that
    project decides; a member of the project cannot."""
    linh, tuan = org_ids["users"]["linh"], org_ids["users"]["tuan"]
    task_port.add(7, org_ids["projects"]["P-TT"], team_ids=[])  # nobody's team
    lead_outcome = service.handle(mk.propose(
        linh, [mk.op_set("task:7", "status", "canceled")]))
    assert lead_outcome["status"] == "effective"

    member_outcome = service.handle(mk.propose(
        tuan, [mk.op_set("task:7", "attr:owner-note", "I'll take it")],
        created_from=CreatedFrom.LLM, confidence=0.9))
    assert member_outcome["status"] == "proposed"


def test_can_decide_is_total_on_unknown_targets(service, org_ids, mk):
    """G48: even an unresolvable target yields a defined answer — apex-only,
    never a crash, never silent effectiveness for a member."""
    duc, linh = org_ids["users"]["duc"], org_ids["users"]["linh"]
    member = service.handle(mk.propose(
        duc, [mk.op_set("task:999", "attr:x", "y")],
        created_from=CreatedFrom.LLM, confidence=0.9))
    assert member["status"] == "proposed"
    assert linh in member["approvers"]

    coordinator = service.handle(mk.propose(
        linh, [mk.op_set("task:999", "attr:x", "y")]))
    assert coordinator["status"] == "effective"


def test_new_task_checked_against_group_team(service, org_ids, mk):
    """G3: NEW_TASK authority is checked against the chat group's team; the
    gateway allocates the task id and rewrites the ops target."""
    linh, tuan = org_ids["users"]["linh"], org_ids["users"]["tuan"]
    g_tt = org_ids["groups"]["G-TT"]
    outcome = service.handle(mk.propose(
        linh, [mk.op_set("NEW_TASK", "description", "làm đèn lồng")],
        scope_target="NEW_TASK", context_group_id=g_tt))
    assert outcome["status"] == "effective"
    assert outcome["new_task_id"] is not None

    member = service.handle(mk.propose(
        tuan, [mk.op_set("NEW_TASK", "description", "một task khác")],
        scope_target="NEW_TASK", context_group_id=g_tt,
        created_from=CreatedFrom.LLM, confidence=0.9))
    assert member["status"] == "proposed"
