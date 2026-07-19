"""DEC-2 — the facet registry as data, not scattered ifs (design-v2 §Facet registry).

The supersession unit is **(scope-target, facet-key)**, refined per facet:
- simple facets (`description`, `status`, dates, `type`, `kind`, `project`):
  one unit per (target, facet); `set` supersedes the occupant.
- `assignment` / `team`: per person-slot / team-slot units
  (`task:1|assignment|user:7`). `add` occupies its slot (an add over a standing
  remove supersedes it — re-assignment); `set` displaces EVERY unit under the
  facet prefix; `remove` supersedes that slot's `add`. Bare "giao X" = add.
- `dependency`: per-edge units; `remove` supersedes the `add`.
- `attr:<name>` (incl. team/project-scope policies): per (target, attr-name).
- `note`: append — never occupies, never supersedes, never conflicts.
- `merge` / cross-project `project` transfer / project-scope `end_date`:
  registered so unit derivation is total; their fold consequences live in B's
  `tasks` module (TSK-4/5/7) and land in later phases.

`unit_key` strings are the shared vocabulary of `effective_units`,
`decision_units`, materialization dedup [EVM-002], and expected-version checks
[EVM-021] — treat the format as frozen: `<target>|<facet>` or
`<target>|<facet>|<slot>`.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from typing import Any

from evermind.contracts.commands import OpSpec


class UnitMode(str, Enum):
    PER_FACET = "per_facet"  # one unit per (target, facet)
    PER_SLOT = "per_slot"  # per person/team slot; `set` displaces the whole facet
    PER_EDGE = "per_edge"  # dependency edges
    NONE = "none"  # note append — no unit, no conflict


@dataclass(frozen=True)
class FacetSpec:
    name: str
    unit_mode: UnitMode
    ops: frozenset[str]


_SIMPLE = frozenset({"set"})

FACET_REGISTRY: dict[str, FacetSpec] = {
    "description": FacetSpec("description", UnitMode.PER_FACET, _SIMPLE),
    # `status` via decisions only for cancel/revive; normal transitions are
    # task_updates and never supersede anything (design-v2 §Facet registry)
    "status": FacetSpec("status", UnitMode.PER_FACET, _SIMPLE),
    "blocked_waiting_on": FacetSpec("blocked_waiting_on", UnitMode.PER_FACET, _SIMPLE),
    "start_date": FacetSpec("start_date", UnitMode.PER_FACET, _SIMPLE),
    "end_date": FacetSpec("end_date", UnitMode.PER_FACET, _SIMPLE),
    "type": FacetSpec("type", UnitMode.PER_FACET, _SIMPLE),
    "kind": FacetSpec("kind", UnitMode.PER_FACET, _SIMPLE),
    "assignment": FacetSpec("assignment", UnitMode.PER_SLOT, frozenset({"add", "remove", "set"})),
    "team": FacetSpec("team", UnitMode.PER_SLOT, frozenset({"add", "remove", "set"})),
    "dependency": FacetSpec("dependency", UnitMode.PER_EDGE, frozenset({"add", "remove"})),
    "note": FacetSpec("note", UnitMode.NONE, frozenset({"append"})),
    "merge": FacetSpec("merge", UnitMode.PER_FACET, _SIMPLE),  # TSK-4 (P6)
    "project": FacetSpec("project", UnitMode.PER_FACET, _SIMPLE),  # TSK-5 transfer (P6)
}


def facet_spec(facet: str) -> FacetSpec:
    """`attr:<name>` facets are dynamic per-facet entries (extractor names the
    attr); everything else must be registered."""
    if facet.startswith("attr:"):
        return FacetSpec(facet, UnitMode.PER_FACET, _SIMPLE)
    spec = FACET_REGISTRY.get(facet)
    if spec is None:
        raise ValueError(f"unknown facet: {facet!r}")
    return spec


def canonical_value(value: Any) -> str:
    """Stable comparison form for the same-value guard (G66)."""
    return json.dumps(value, sort_keys=True, ensure_ascii=False, default=str)


def _slot_suffix(facet: str, value: Any) -> str:
    """Person/team slot identity. Accepts raw ids, "user:7"-style strings, or
    {"user_id": 7} dicts from the extractor."""
    if isinstance(value, dict):
        for key in ("user_id", "user", "team_id", "team", "id"):
            if key in value:
                return str(value[key])
        return canonical_value(value)
    return str(value)


def _edge_suffix(value: Any) -> str:
    if isinstance(value, dict):
        pred = value.get("predecessor_task_id") or value.get("predecessor")
        succ = value.get("successor_task_id") or value.get("successor")
        if pred is not None or succ is not None:
            return f"{pred}->{succ}"
        return canonical_value(value)
    return str(value)


def unit_key_for_op(op: OpSpec) -> str | None:
    """The unit this op occupies when effective. None => no unit (note append)."""
    spec = facet_spec(op.facet)
    if op.op not in spec.ops:
        raise ValueError(f"facet {op.facet!r} does not allow op {op.op!r}")
    if spec.unit_mode is UnitMode.NONE:
        return None
    if spec.unit_mode is UnitMode.PER_FACET:
        return f"{op.target}|{spec.name}"
    if spec.unit_mode is UnitMode.PER_EDGE:
        return f"{op.target}|{spec.name}|{_edge_suffix(op.value)}"
    # PER_SLOT: `set` occupies the bare facet unit and displaces every slot
    if op.op == "set":
        return f"{op.target}|{spec.name}"
    return f"{op.target}|{spec.name}|{_slot_suffix(op.facet, op.value)}"


def displaced_prefix_for_op(op: OpSpec) -> str | None:
    """For slot-facet `set` ops: every unit under this prefix is displaced
    ("`set` supersedes all prior assignment ops")."""
    spec = facet_spec(op.facet)
    if spec.unit_mode is UnitMode.PER_SLOT and op.op == "set":
        return f"{op.target}|{spec.name}"
    return None


@dataclass
class UnitPlan:
    """Everything the effective-write transaction needs from the ops list."""

    occupied_units: list[str]  # units the decision occupies when effective
    displaced_prefixes: list[str]  # slot-facet `set` displacement prefixes
    unit_values: dict[str, tuple[str, str]]  # unit -> (op, canonical value)
    task_ids: list[int]  # distinct "task:N" targets, for decision_tasks
    has_new_task: bool


def derive_unit_plan(ops: list[OpSpec]) -> UnitPlan:
    occupied: list[str] = []
    prefixes: list[str] = []
    values: dict[str, tuple[str, str]] = {}
    task_ids: list[int] = []
    has_new_task = False
    for op in ops:
        if op.target == "NEW_TASK":
            has_new_task = True
        elif op.target.startswith("task:"):
            task_id = int(op.target.split(":", 1)[1])
            if task_id not in task_ids:
                task_ids.append(task_id)
        unit = unit_key_for_op(op)
        if unit is not None:
            if unit not in occupied:
                occupied.append(unit)
            values[unit] = (op.op, canonical_value(op.value))
        prefix = displaced_prefix_for_op(op)
        if prefix is not None and prefix not in prefixes:
            prefixes.append(prefix)
    return UnitPlan(occupied_units=occupied, displaced_prefixes=prefixes,
                    unit_values=values, task_ids=task_ids, has_new_task=has_new_task)
