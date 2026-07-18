"""L1 — ordering & late arrival (S10 order half, S15). Pins: event-ts fold
direction, born-already-superseded (G31), the deterministic tiebreak [EVM-012].
ING-7 is Lane A's birth-side half; B's fold replays the same order."""
from __future__ import annotations

from datetime import timedelta

from evermind.contracts.enums import CreatedFrom, DecisionStatus
from evermind.decisions.models import Decision


def test_late_older_decision_born_already_superseded(service, task_port, org_ids, mk,
                                                     db_session):
    """G31: a late-arriving decision OLDER (event ts) than the standing
    same-unit effective one enters history as `superseded` — the present is
    undisturbed."""
    linh = org_ids["users"]["linh"]
    task_port.add(1, org_ids["projects"]["P-TT"], team_ids=[org_ids["teams"]["TEAM-EV"]])
    standing = service.handle(mk.propose(
        linh, [mk.op_set("task:1", "attr:venue", "school")], ts=mk.ago(hours=1)))
    assert standing["status"] == "effective"

    late = service.handle(mk.propose(
        linh, [mk.op_set("task:1", "attr:venue", "park")], ts=mk.ago(hours=3)))
    assert late["status"] == "already_superseded"
    assert late["superseded_by"] == standing["decision_id"]

    born_superseded = db_session.get(Decision, late["decision_id"])
    assert born_superseded.status is DecisionStatus.SUPERSEDED
    assert born_superseded.superseded_by_decision_id == standing["decision_id"]
    # the standing decision is untouched — never flipped, never re-pointed
    assert db_session.get(Decision, standing["decision_id"]).status is DecisionStatus.EFFECTIVE


def test_newer_ts_supersedes_normally(service, task_port, org_ids, mk, db_session):
    """The mirror case: newer event-ts wins the unit exactly as a live write."""
    linh = org_ids["users"]["linh"]
    task_port.add(1, org_ids["projects"]["P-TT"], team_ids=[org_ids["teams"]["TEAM-EV"]])
    older = service.handle(mk.propose(
        linh, [mk.op_set("task:1", "attr:venue", "school")], ts=mk.ago(hours=3)))
    newer = service.handle(mk.propose(
        linh, [mk.op_set("task:1", "attr:venue", "park")], ts=mk.ago(hours=1)))
    assert newer["status"] == "effective"
    assert older["decision_id"] in newer["superseded"]


def test_equal_ts_tiebreak_on_recorded_at(service, task_port, org_ids, mk):
    """[EVM-012]: fold order is (ts, recorded_at, stable_event_id) — with equal
    event ts, the later-recorded decision is the newer one and supersedes."""
    linh = org_ids["users"]["linh"]
    task_port.add(1, org_ids["projects"]["P-TT"], team_ids=[org_ids["teams"]["TEAM-EV"]])
    same_ts = mk.ago(hours=2)
    first = service.handle(mk.propose(
        linh, [mk.op_set("task:1", "attr:venue", "school")], ts=same_ts))
    second = service.handle(mk.propose(
        linh, [mk.op_set("task:1", "attr:venue", "park")], ts=same_ts))
    assert second["status"] == "effective"  # recorded later -> newer -> supersedes
    assert first["decision_id"] in second["superseded"]


def test_impossible_chronology_goes_to_triage(service, org_ids, mk, db_session):
    """[EVM-012]: a far-future event ts is impossible chronology — triage,
    never a silent write."""
    linh = org_ids["users"]["linh"]
    outcome = service.handle(mk.propose(
        linh, [mk.op_set("task:1", "attr:venue", "moon")],
        ts=mk.now() + timedelta(days=30), created_from=CreatedFrom.LLM))
    assert outcome["status"] == "triage"
    assert db_session.query(Decision).count() == 0
