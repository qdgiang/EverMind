"""L1 — proposal hygiene (S28, S43). Pins: dedup-merge (G49), change-of-mind
withdrawal (settled #17b), bulk acts (DEC-7), **no expiry ever** (settled #18)."""
from __future__ import annotations

import uuid

from sqlalchemy import select

from evermind.contracts.commands import BulkProposalAction
from evermind.contracts.enums import CreatedFrom, DecisionStatus, RejectedReason
from evermind.decisions.models import Decision, DecisionCitation


def test_same_value_pendings_merge(service, task_port, org_ids, mk, db_session):
    """G49: a new proposal matching a pending one on (unit, op, value) merges
    into it — citations union, one queue entry."""
    duc, tuan = org_ids["users"]["duc"], org_ids["users"]["tuan"]
    task_port.add(1, org_ids["projects"]["P-TT"], team_ids=[org_ids["teams"]["TEAM-EV"]])
    first = service.handle(mk.propose(
        duc, [mk.op_set("task:1", "attr:quantity", 100)],
        created_from=CreatedFrom.LLM, confidence=0.9,
        citations=[mk.cite(message_id=11)]))
    assert first["status"] == "proposed"

    second = service.handle(mk.propose(
        tuan, [mk.op_set("task:1", "attr:quantity", 100)],
        created_from=CreatedFrom.LLM, confidence=0.9,
        citations=[mk.cite(message_id=22)]))
    assert second["status"] == "merged_into_pending"
    assert second["decision_id"] == first["decision_id"]

    cited = set(db_session.scalars(select(DecisionCitation.message_id).where(
        DecisionCitation.decision_id == first["decision_id"])))
    assert {11, 22} <= cited  # citations unioned
    # only ONE pending decision exists for the unit
    pendings = list(db_session.scalars(select(Decision).where(
        Decision.status == DecisionStatus.PROPOSED)))
    assert len(pendings) == 1


def test_change_of_mind_withdraws_own_older(service, task_port, org_ids, mk, db_session):
    """Settled #17b: a proposer's own different-value proposal on the same unit
    withdraws their older pending — linked, never expired."""
    duc = org_ids["users"]["duc"]
    task_port.add(1, org_ids["projects"]["P-TT"], team_ids=[org_ids["teams"]["TEAM-EV"]])
    first = service.handle(mk.propose(
        duc, [mk.op_set("task:1", "attr:quantity", 100)],
        created_from=CreatedFrom.LLM, confidence=0.9))
    second = service.handle(mk.propose(
        duc, [mk.op_set("task:1", "attr:quantity", 150)],
        created_from=CreatedFrom.LLM, confidence=0.9))
    assert second["status"] == "proposed"
    assert first["decision_id"] in second["withdrawn"]

    old = db_session.get(Decision, first["decision_id"])
    assert old.status is DecisionStatus.REJECTED
    assert old.rejected_reason is RejectedReason.WITHDRAWN
    assert old.superseded_by_decision_id == second["decision_id"]


def test_different_proposers_stay_separate(service, task_port, org_ids, mk, db_session):
    """G49: same-unit different-value pendings from DIFFERENT proposers are
    real alternatives — both stay open."""
    duc, tuan = org_ids["users"]["duc"], org_ids["users"]["tuan"]
    task_port.add(1, org_ids["projects"]["P-TT"], team_ids=[org_ids["teams"]["TEAM-EV"]])
    first = service.handle(mk.propose(
        duc, [mk.op_set("task:1", "attr:quantity", 100)],
        created_from=CreatedFrom.LLM, confidence=0.9))
    second = service.handle(mk.propose(
        tuan, [mk.op_set("task:1", "attr:quantity", 150)],
        created_from=CreatedFrom.LLM, confidence=0.9))
    assert first["status"] == "proposed"
    assert second["status"] == "proposed"
    assert db_session.get(Decision, first["decision_id"]).status is DecisionStatus.PROPOSED
    assert db_session.get(Decision, second["decision_id"]).status is DecisionStatus.PROPOSED


def test_no_expiry_ever(service, task_port, org_ids, mk, db_session):
    """Settled #18: a proposal stays `proposed` through arbitrary later writes
    elsewhere — only a human act resolves it. (No TTL column even exists.)"""
    duc, linh = org_ids["users"]["duc"], org_ids["users"]["linh"]
    task_port.add(1, org_ids["projects"]["P-TT"], team_ids=[org_ids["teams"]["TEAM-EV"]])
    pending = service.handle(mk.propose(
        duc, [mk.op_set("task:1", "attr:quantity", 100)],
        created_from=CreatedFrom.LLM, confidence=0.9))
    # unrelated activity on other units
    for i in range(5):
        service.handle(mk.propose(linh, [mk.op_set("task:1", f"attr:other-{i}", i)]))
    decision = db_session.get(Decision, pending["decision_id"])
    assert decision.status is DecisionStatus.PROPOSED
    assert not hasattr(decision, "approval_deadline")  # the column must not exist
    assert "expired" not in {r.value for r in RejectedReason}


def test_bulk_dismiss_all_from(service, task_port, org_ids, mk, db_session):
    """DEC-7: dismiss-all-from-person is an explicit approver act —
    rejected(dismissed), visible under show-inactive."""
    duc, tuan, linh = (org_ids["users"]["duc"], org_ids["users"]["tuan"],
                       org_ids["users"]["linh"])
    task_port.add(1, org_ids["projects"]["P-TT"], team_ids=[org_ids["teams"]["TEAM-EV"]])
    from_duc = service.handle(mk.propose(
        duc, [mk.op_set("task:1", "attr:a", 1)], created_from=CreatedFrom.LLM,
        confidence=0.9))
    from_tuan = service.handle(mk.propose(
        tuan, [mk.op_set("task:1", "attr:b", 2)], created_from=CreatedFrom.LLM,
        confidence=0.9))

    outcome = service.handle(BulkProposalAction(
        client_command_id=uuid.uuid4(), persona="user-linh",
        created_from=CreatedFrom.DASHBOARD, actor_user_id=linh,
        action="dismiss_all_from", from_user_id=duc))
    assert from_duc["decision_id"] in outcome["acted"]
    assert from_tuan["decision_id"] not in outcome["acted"]

    dismissed = db_session.get(Decision, from_duc["decision_id"])
    assert dismissed.status is DecisionStatus.REJECTED
    assert dismissed.rejected_reason is RejectedReason.DISMISSED
    assert db_session.get(Decision, from_tuan["decision_id"]).status is DecisionStatus.PROPOSED


def test_bulk_approve_all(service, task_port, org_ids, mk, db_session):
    """DEC-7: approve-all effects every pending the actor is authorized for."""
    duc, linh = org_ids["users"]["duc"], org_ids["users"]["linh"]
    task_port.add(1, org_ids["projects"]["P-TT"], team_ids=[org_ids["teams"]["TEAM-EV"]])
    a = service.handle(mk.propose(
        duc, [mk.op_set("task:1", "attr:a", 1)], created_from=CreatedFrom.LLM,
        confidence=0.9))
    b = service.handle(mk.propose(
        duc, [mk.op_set("task:1", "attr:b", 2)], created_from=CreatedFrom.LLM,
        confidence=0.9))
    outcome = service.handle(BulkProposalAction(
        client_command_id=uuid.uuid4(), persona="user-linh",
        created_from=CreatedFrom.DASHBOARD, actor_user_id=linh, action="approve_all"))
    assert set(outcome["acted"]) == {a["decision_id"], b["decision_id"]}
    for decision_id in outcome["acted"]:
        assert db_session.get(Decision, decision_id).status is DecisionStatus.EFFECTIVE
