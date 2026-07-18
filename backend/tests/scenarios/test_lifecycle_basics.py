"""L1 — lifecycle basics (testing-strategy.md; derived from S1/S2/S3/S5).

Pins: born-effective gates (DEC-1), confidence gate (G19), rank gate (G10),
sweep→overruled (G11/G12), veto + resurrection (G17/G18), same-value guard
(G66), approval snapshots [EVM-005].
"""
from __future__ import annotations

import uuid

from sqlalchemy import select

from evermind.contracts.commands import ApproveProposal, RejectProposal
from evermind.contracts.enums import CreatedFrom, DecisionStatus, RejectedReason
from evermind.decisions.models import Decision, DecisionCitation, EffectiveUnit


def _approve(service, decision_id: int, approver: int, **kwargs):
    return service.handle(ApproveProposal(
        client_command_id=uuid.uuid4(), persona=f"user-{approver}",
        created_from=CreatedFrom.DASHBOARD, decision_id=decision_id,
        approved_by_user_id=approver, **kwargs))


def test_authorized_marker_born_effective(service, task_port, org_ids, mk, db_session):
    """S1/G10: an authorized maker's marker decision is born effective."""
    linh = org_ids["users"]["linh"]
    ev = org_ids["teams"]["TEAM-EV"]
    task_port.add(1, org_ids["projects"]["P-TT"], team_ids=[ev])
    outcome = service.handle(mk.propose(linh, [mk.op_set("task:1", "attr:venue", "Nguyen Du")]))
    assert outcome["status"] == "effective"
    decision = db_session.get(Decision, outcome["decision_id"])
    assert decision.status is DecisionStatus.EFFECTIVE
    assert decision.decided_by_role_at_time == 3  # rank snapshot (G10)
    assert decision.confidence == 1.0  # markers are human-asserted


def test_member_proposal_waits_then_approved(service, task_port, org_ids, mk, db_session):
    """S1/S3: an unauthorized member's candidate is born proposed and becomes
    effective only via the approver's act, with the at-act snapshot [EVM-005]."""
    duc, linh = org_ids["users"]["duc"], org_ids["users"]["linh"]
    task_port.add(1, org_ids["projects"]["P-TT"], team_ids=[org_ids["teams"]["TEAM-EV"]])
    outcome = service.handle(mk.propose(
        duc, [mk.op_set("task:1", "attr:quantity", 120)],
        created_from=CreatedFrom.LLM, confidence=0.95))
    assert outcome["status"] == "proposed"
    assert outcome["hold_reason"] == "unauthorized"
    assert linh in outcome["approvers"]

    approved = _approve(service, outcome["decision_id"], linh)
    assert approved["status"] == "effective"
    decision = db_session.get(Decision, outcome["decision_id"])
    assert decision.approved_by_user_id == linh
    assert decision.approved_by_role_at_act == 3  # [EVM-005] at-act snapshot
    assert decision.approval_via.value == "authority"


def test_confidence_gate_below_tau(service, task_port, org_ids, mk, db_session):
    """G19: an authorized maker's low-confidence extraction is born proposed —
    never silently dropped; their own confirm is `self_confirm`."""
    linh = org_ids["users"]["linh"]
    task_port.add(1, org_ids["projects"]["P-TT"], team_ids=[org_ids["teams"]["TEAM-EV"]])
    outcome = service.handle(mk.propose(
        linh, [mk.op_set("task:1", "attr:budget", "5tr")],
        created_from=CreatedFrom.LLM, confidence=0.5))
    assert outcome["status"] == "proposed"
    assert outcome["hold_reason"] == "below_tau"

    approved = _approve(service, outcome["decision_id"], linh)
    assert approved["status"] == "effective"
    decision = db_session.get(Decision, outcome["decision_id"])
    assert decision.approval_via.value == "self_confirm"


def test_rank_gate_holds_lower_rank_supersession(service, task_port, org_ids, mk):
    """G10: rank(actor) must be >= the standing maker's snapshotted rank —
    a lead cannot silently supersede the coordinator's decision."""
    linh, mai = org_ids["users"]["linh"], org_ids["users"]["mai"]
    ed = org_ids["teams"]["TEAM-ED"]
    task_port.add(2, org_ids["projects"]["P-CL"], team_ids=[ed])
    first = service.handle(mk.propose(linh, [mk.op_set("task:2", "attr:venue", "hall A")]))
    assert first["status"] == "effective"

    second = service.handle(mk.propose(mai, [mk.op_set("task:2", "attr:venue", "hall B")]))
    assert second["status"] == "proposed"
    assert second["hold_reason"] == "rank_gate"
    assert second["standing_decision_id"] == first["decision_id"]


def test_effective_write_sweeps_pendings_overruled(service, task_port, org_ids, mk,
                                                   db_session):
    """S3 + G11/G12: apple→peach — an authority's same-unit effective write
    flips the standing decision to superseded AND sweeps competing pendings to
    rejected(overruled) with superseded_by = the winner."""
    duc, linh = org_ids["users"]["duc"], org_ids["users"]["linh"]
    task_port.add(1, org_ids["projects"]["P-TT"], team_ids=[org_ids["teams"]["TEAM-EV"]])
    standing = service.handle(mk.propose(linh, [mk.op_set("task:1", "attr:fruit", "apple")]))
    pending = service.handle(mk.propose(
        duc, [mk.op_set("task:1", "attr:fruit", "banana")],
        created_from=CreatedFrom.LLM, confidence=0.9))
    assert pending["status"] == "proposed"

    winner = service.handle(mk.propose(linh, [mk.op_set("task:1", "attr:fruit", "peach")]))
    assert winner["status"] == "effective"
    assert standing["decision_id"] in winner["superseded"]
    assert pending["decision_id"] in winner["swept_overruled"]

    old = db_session.get(Decision, standing["decision_id"])
    assert old.status is DecisionStatus.SUPERSEDED
    assert old.superseded_by_decision_id == winner["decision_id"]
    swept = db_session.get(Decision, pending["decision_id"])
    assert swept.status is DecisionStatus.REJECTED
    assert swept.rejected_reason is RejectedReason.OVERRULED
    assert swept.superseded_by_decision_id == winner["decision_id"]


def test_veto_resurrects_predecessor(service, task_port, org_ids, mk, db_session):
    """S5 + G17: rejecting an effective decision restores what it superseded
    (iff no other effective superseder) and re-occupies the unit."""
    linh = org_ids["users"]["linh"]
    task_port.add(1, org_ids["projects"]["P-TT"], team_ids=[org_ids["teams"]["TEAM-EV"]])
    first = service.handle(mk.propose(linh, [mk.op_set("task:1", "attr:venue", "school")]))
    second = service.handle(mk.propose(linh, [mk.op_set("task:1", "attr:venue", "park")]))
    assert second["superseded"] == [first["decision_id"]]

    veto = service.handle(RejectProposal(
        client_command_id=uuid.uuid4(), persona="user-linh",
        created_from=CreatedFrom.DASHBOARD, decision_id=second["decision_id"],
        rejected_by_user_id=linh, reason="veto"))
    assert veto["status"] == "rejected"
    assert veto["resurrected"] == [first["decision_id"]]

    restored = db_session.get(Decision, first["decision_id"])
    assert restored.status is DecisionStatus.EFFECTIVE
    assert restored.superseded_by_decision_id is None
    occupant = db_session.scalar(select(EffectiveUnit.decision_id).where(
        EffectiveUnit.unit_key == "task:1|attr:venue"))
    assert occupant == first["decision_id"]


def test_challenge_filed_by_insufficient_rank(service, task_port, org_ids, mk, db_session):
    """G18: someone below the maker's rank cannot veto — the act files a
    challenge for the maker to resolve; the decision stands."""
    duc, linh = org_ids["users"]["duc"], org_ids["users"]["linh"]
    task_port.add(1, org_ids["projects"]["P-TT"], team_ids=[org_ids["teams"]["TEAM-EV"]])
    standing = service.handle(mk.propose(linh, [mk.op_set("task:1", "attr:venue", "school")]))

    challenge = service.handle(RejectProposal(
        client_command_id=uuid.uuid4(), persona="user-duc",
        created_from=CreatedFrom.DASHBOARD, decision_id=standing["decision_id"],
        rejected_by_user_id=duc, reason="veto"))
    assert challenge["status"] == "challenge_filed"
    assert db_session.get(Decision, standing["decision_id"]).status is DecisionStatus.EFFECTIVE


def test_same_value_guard_corroborates(service, task_port, org_ids, mk, db_session):
    """G66: a candidate equal (op+value) to the standing unit becomes a
    corroborating citation — never a new decision; attribution never moves."""
    duc, linh = org_ids["users"]["duc"], org_ids["users"]["linh"]
    task_port.add(1, org_ids["projects"]["P-TT"], team_ids=[org_ids["teams"]["TEAM-EV"]])
    standing = service.handle(mk.propose(linh, [mk.op_set("task:1", "attr:budget", "5tr")]))

    restatement = service.handle(mk.propose(
        duc, [mk.op_set("task:1", "attr:budget", "5tr")],
        created_from=CreatedFrom.LLM, confidence=0.9,
        citations=[mk.cite(message_id=109)]))
    assert restatement["status"] == "corroborated"
    assert restatement["decision_ids"] == [standing["decision_id"]]

    decision = db_session.get(Decision, standing["decision_id"])
    assert decision.decided_by_user_id == linh  # attribution never moves
    corroboration = db_session.scalar(select(DecisionCitation).where(
        DecisionCitation.decision_id == standing["decision_id"],
        DecisionCitation.message_id == 109))
    assert corroboration is not None
    assert corroboration.kind.value == "corroboration"
    # no second decision row was created
    assert db_session.scalar(
        select(Decision).where(Decision.decided_by_user_id == duc)) is None
