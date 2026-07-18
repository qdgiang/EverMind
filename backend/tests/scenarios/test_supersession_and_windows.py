"""L1 — supersession & effect windows (S9, S17). Pins: effect-window shadowing
(G42), exception never supersedes, overlap → hold [EVM-004]."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import select

from evermind.contracts.enums import DecisionStatus
from evermind.decisions.models import Decision, EffectiveUnit


def _window(a: str, b: str) -> tuple[datetime, datetime]:
    return (datetime.fromisoformat(a), datetime.fromisoformat(b))


def test_effect_window_shadows_never_supersedes(service, org_ids, mk, db_session):
    """G42: DC-05 shadows DC-01 inside its window; the standing policy stays
    effective and keeps its unit — no supersession, no status change."""
    mai = org_ids["users"]["mai"]
    ed = org_ids["teams"]["TEAM-ED"]
    standing = service.handle(mk.propose(
        mai, [mk.op_set(f"team:{ed}", "attr:class-schedule", "Sun 9:00")],
        scope_target=f"team:{ed}"))
    assert standing["status"] == "effective"

    exception = service.handle(mk.propose(
        mai, [mk.op_set(f"team:{ed}", "attr:class-schedule", "no class")],
        scope_target=f"team:{ed}",
        effect_window=_window("2026-09-20T00:00:00", "2026-09-20T23:59:59")))
    assert exception["status"] == "effective"
    assert exception["windowed"] is True

    # the standing decision is untouched and still owns the unit
    assert db_session.get(Decision, standing["decision_id"]).status is DecisionStatus.EFFECTIVE
    occupant = db_session.scalar(select(EffectiveUnit.decision_id).where(
        EffectiveUnit.unit_key == f"team:{ed}|attr:class-schedule"))
    assert occupant == standing["decision_id"]
    # both are simultaneously effective — the window shadows, it does not occupy
    assert db_session.get(Decision, exception["decision_id"]).status is DecisionStatus.EFFECTIVE


def test_overlapping_windows_hold_the_later(service, org_ids, mk):
    """[EVM-004]: a second effect-window overlapping the first on the same unit
    is held `proposed` for a human — never two active shadows."""
    mai = org_ids["users"]["mai"]
    ed = org_ids["teams"]["TEAM-ED"]
    service.handle(mk.propose(
        mai, [mk.op_set(f"team:{ed}", "attr:class-schedule", "standing")],
        scope_target=f"team:{ed}"))
    first = service.handle(mk.propose(
        mai, [mk.op_set(f"team:{ed}", "attr:class-schedule", "window A")],
        scope_target=f"team:{ed}",
        effect_window=_window("2026-09-19T00:00:00", "2026-09-21T00:00:00")))
    assert first["status"] == "effective"

    second = service.handle(mk.propose(
        mai, [mk.op_set(f"team:{ed}", "attr:class-schedule", "window B")],
        scope_target=f"team:{ed}",
        effect_window=_window("2026-09-20T00:00:00", "2026-09-22T00:00:00")))
    assert second["status"] == "proposed"
    assert second["hold_reason"] == "overlap_hold"
    assert second["overlaps_decision_id"] == first["decision_id"]


def test_disjoint_windows_both_effective(service, org_ids, mk):
    """[EVM-004] boundary: non-overlapping windows on one unit are both fine."""
    mai = org_ids["users"]["mai"]
    ed = org_ids["teams"]["TEAM-ED"]
    service.handle(mk.propose(
        mai, [mk.op_set(f"team:{ed}", "attr:class-schedule", "standing")],
        scope_target=f"team:{ed}"))
    first = service.handle(mk.propose(
        mai, [mk.op_set(f"team:{ed}", "attr:class-schedule", "window A")],
        scope_target=f"team:{ed}",
        effect_window=_window("2026-09-01T00:00:00", "2026-09-02T00:00:00")))
    second = service.handle(mk.propose(
        mai, [mk.op_set(f"team:{ed}", "attr:class-schedule", "window B")],
        scope_target=f"team:{ed}",
        effect_window=_window("2026-09-10T00:00:00", "2026-09-11T00:00:00")))
    assert first["status"] == "effective"
    assert second["status"] == "effective"


def test_assignment_slots_multi_pic(service, task_port, org_ids, mk, db_session):
    """G1: per-person-slot assignment ops — `add` never displaces another
    person's slot (multi-PIC); `set` supersedes ALL prior assignment ops."""
    linh = org_ids["users"]["linh"]
    duc, minh = org_ids["users"]["duc"], org_ids["users"]["minh"]
    task_port.add(1, org_ids["projects"]["P-TT"], team_ids=[org_ids["teams"]["TEAM-EV"]])

    add_duc = service.handle(mk.propose(
        linh, [mk.OpSpec(target="task:1", facet="assignment", op="add", value=duc)]))
    add_minh = service.handle(mk.propose(
        linh, [mk.OpSpec(target="task:1", facet="assignment", op="add", value=minh)]))
    assert add_duc["status"] == "effective"
    assert add_minh["status"] == "effective"
    assert add_duc["decision_id"] not in add_minh["superseded"]  # both slots live

    set_all = service.handle(mk.propose(
        linh, [mk.OpSpec(target="task:1", facet="assignment", op="set", value=[minh])]))
    assert set_all["status"] == "effective"
    assert set(set_all["superseded"]) == {add_duc["decision_id"], add_minh["decision_id"]}


def test_remove_supersedes_that_persons_add(service, task_port, org_ids, mk):
    """Facet registry: `remove` supersedes that person's `add` — other slots
    untouched."""
    linh = org_ids["users"]["linh"]
    duc, minh = org_ids["users"]["duc"], org_ids["users"]["minh"]
    task_port.add(1, org_ids["projects"]["P-TT"], team_ids=[org_ids["teams"]["TEAM-EV"]])
    add_duc = service.handle(mk.propose(
        linh, [mk.OpSpec(target="task:1", facet="assignment", op="add", value=duc)]))
    add_minh = service.handle(mk.propose(
        linh, [mk.OpSpec(target="task:1", facet="assignment", op="add", value=minh)]))

    remove_duc = service.handle(mk.propose(
        linh, [mk.OpSpec(target="task:1", facet="assignment", op="remove", value=duc)]))
    assert remove_duc["status"] == "effective"
    assert remove_duc["superseded"] == [add_duc["decision_id"]]
    assert add_minh["decision_id"] not in remove_duc["superseded"]


def test_note_append_never_conflicts(service, task_port, org_ids, mk):
    """Facet registry: note append occupies no unit and supersedes nothing."""
    linh = org_ids["users"]["linh"]
    task_port.add(1, org_ids["projects"]["P-TT"], team_ids=[org_ids["teams"]["TEAM-EV"]])
    first = service.handle(mk.propose(
        linh, [mk.OpSpec(target="task:1", facet="note", op="append", value="note 1")]))
    second = service.handle(mk.propose(
        linh, [mk.OpSpec(target="task:1", facet="note", op="append", value="note 2")]))
    assert first["status"] == "effective"
    assert second["status"] == "effective"
    assert second["superseded"] == []
