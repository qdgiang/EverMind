"""L1 — multi-op atomicity [EVM-003]. Pins: all-or-nothing, highest-authority
routing, per-unit downstream supersession, no bundle entity."""
from __future__ import annotations

from sqlalchemy import select

from evermind.contracts.enums import CreatedFrom, DecisionScope
from evermind.decisions.models import Decision, DecisionUnit, EffectiveUnit


def test_multi_op_occupies_all_units_as_one_row(service, task_port, org_ids, mk,
                                                db_session):
    """One decision row, several units occupied on success — no bundle entity."""
    linh = org_ids["users"]["linh"]
    task_port.add(1, org_ids["projects"]["P-TT"], team_ids=[org_ids["teams"]["TEAM-EV"]])
    outcome = service.handle(mk.propose(linh, [
        mk.op_set("task:1", "attr:budget", "5tr"),
        mk.op_set("task:1", "end_date", "2026-09-25"),
    ]))
    assert outcome["status"] == "effective"
    units = set(db_session.scalars(select(DecisionUnit.unit_key).where(
        DecisionUnit.decision_id == outcome["decision_id"])))
    assert units == {"task:1|attr:budget", "task:1|end_date"}
    for unit in units:
        assert db_session.scalar(select(EffectiveUnit.decision_id).where(
            EffectiveUnit.unit_key == unit)) == outcome["decision_id"]
    assert db_session.query(Decision).count() == 1


def test_routed_whole_to_highest_authority(service, task_port, org_ids, mk, db_session):
    """[EVM-003]: if ANY op requires a higher authority, the WHOLE decision is
    held — a lead cannot smuggle a project-policy op inside a task decision."""
    mai = org_ids["users"]["mai"]
    ed = org_ids["teams"]["TEAM-ED"]
    cl = org_ids["projects"]["P-CL"]
    task_port.add(2, cl, team_ids=[ed])
    outcome = service.handle(mk.propose(
        mai,
        [
            mk.op_set("task:2", "attr:slot", "9:00"),  # mai alone could do this
            mk.op_set(f"project:{cl}", "attr:budget-cap", "99tr"),  # she cannot
        ],
        scope=DecisionScope.PROJECT, scope_target=f"project:{cl}",
        created_from=CreatedFrom.DASHBOARD))
    assert outcome["status"] == "proposed"  # all-or-nothing: nothing took effect
    for unit in ("task:2|attr:slot", f"project:{cl}|attr:budget-cap"):
        assert db_session.scalar(select(EffectiveUnit).where(
            EffectiveUnit.unit_key == unit)) is None


def test_multi_op_superseded_per_unit_downstream(service, task_port, org_ids, mk,
                                                 db_session):
    """Per-unit downstream supersession: a later single-op decision displaces
    the multi-op row on THAT unit only; the multi-op decision itself flips
    superseded (its remaining unit values live on in history)."""
    linh = org_ids["users"]["linh"]
    task_port.add(1, org_ids["projects"]["P-TT"], team_ids=[org_ids["teams"]["TEAM-EV"]])
    multi = service.handle(mk.propose(linh, [
        mk.op_set("task:1", "attr:budget", "5tr"),
        mk.op_set("task:1", "attr:venue", "school"),
    ]))
    single = service.handle(mk.propose(
        linh, [mk.op_set("task:1", "attr:venue", "park")]))
    assert single["status"] == "effective"
    assert multi["decision_id"] in single["superseded"]
    # the untouched unit is vacated with its decision (append-only history keeps
    # the value; the current model has no partial-occupancy row)
    budget_owner = db_session.scalar(select(EffectiveUnit.decision_id).where(
        EffectiveUnit.unit_key == "task:1|attr:budget"))
    assert budget_owner is None
