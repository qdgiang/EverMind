"""Data-driven facet validation and deterministic supersession units (DEC-2)."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Callable, Iterable, Mapping

from evermind.contracts.commands import OpSpec


@dataclass(frozen=True)
class FacetRule:
    key: str
    prefix: bool
    operations: frozenset[str]
    unit_strategy: str
    occupies: bool = True


@dataclass(frozen=True)
class DerivedUnit:
    unit_key: str
    target: str
    facet: str
    op: str
    canonical_value: str
    occupies: bool
    conflict_prefix: str | None = None


_RULES = (
    FacetRule("description", False, frozenset({"set"}), "facet"),
    FacetRule("status", False, frozenset({"set"}), "facet"),
    FacetRule("start_date", False, frozenset({"set"}), "facet"),
    FacetRule("end_date", False, frozenset({"set"}), "facet"),
    FacetRule("type", False, frozenset({"set"}), "facet"),
    FacetRule("kind", False, frozenset({"set"}), "facet"),
    FacetRule("project", False, frozenset({"set"}), "facet"),
    FacetRule("merge", False, frozenset({"set"}), "facet"),
    FacetRule("assignment", False, frozenset({"add", "remove", "set"}), "slot"),
    FacetRule("team", False, frozenset({"add", "remove", "set"}), "slot"),
    FacetRule("dependency", False, frozenset({"add", "remove"}), "edge"),
    FacetRule("attr:", True, frozenset({"set"}), "facet"),
    FacetRule("note", False, frozenset({"append"}), "append", occupies=False),
)


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _slot_token(value: Any) -> str:
    return sha256(_canonical(value).encode()).hexdigest()[:16]


def _facet_unit(op: OpSpec, _stable_event_id: str, _index: int) -> list[str]:
    return [f"v1|{op.target}|{op.facet}"]


def _slot_unit(op: OpSpec, _stable_event_id: str, _index: int) -> list[str]:
    if op.op == "set":
        return [f"v1|{op.target}|{op.facet}|*"]
    return [f"v1|{op.target}|{op.facet}|slot:{_slot_token(op.value)}"]


def _edge_unit(op: OpSpec, _stable_event_id: str, _index: int) -> list[str]:
    return [f"v1|{op.target}|{op.facet}|edge:{_slot_token(op.value)}"]


def _append_unit(op: OpSpec, stable_event_id: str, index: int) -> list[str]:
    token = _slot_token({"event": stable_event_id, "index": index})
    return [f"v1|{op.target}|{op.facet}|append:{token}"]


_UNIT_BUILDERS: Mapping[str, Callable[[OpSpec, str, int], list[str]]] = {
    "facet": _facet_unit,
    "slot": _slot_unit,
    "edge": _edge_unit,
    "append": _append_unit,
}


class FacetRegistry:
    def __init__(self, rules: Iterable[FacetRule]):
        self._rules = tuple(rules)

    @classmethod
    def default(cls) -> FacetRegistry:
        return cls(_RULES)

    def _rule_for(self, facet: str) -> FacetRule:
        for rule in self._rules:
            if (rule.prefix and facet.startswith(rule.key) and facet != rule.key) or (
                not rule.prefix and facet == rule.key
            ):
                return rule
        raise ValueError(f"unsupported facet: {facet}")

    def derive_units(
        self,
        ops: Iterable[OpSpec],
        *,
        stable_event_id: str,
    ) -> list[DerivedUnit]:
        units: list[DerivedUnit] = []
        for index, op in enumerate(ops):
            rule = self._rule_for(op.facet)
            if op.op not in rule.operations:
                raise ValueError(f"unsupported op {op.op!r} for facet {op.facet!r}")
            conflict_prefix = None
            if rule.unit_strategy == "slot" and op.op == "set":
                conflict_prefix = f"v1|{op.target}|{op.facet}|"
            for unit_key in _UNIT_BUILDERS[rule.unit_strategy](op, stable_event_id, index):
                units.append(
                    DerivedUnit(
                        unit_key=unit_key,
                        target=op.target,
                        facet=op.facet,
                        op=op.op,
                        canonical_value=_canonical(op.value),
                        occupies=rule.occupies,
                        conflict_prefix=conflict_prefix,
                    )
                )
        keys = [unit.unit_key for unit in units]
        if len(keys) != len(set(keys)):
            raise ValueError("multi-op decision contains the same supersession unit twice")
        return units


def version_for_bindings(bindings: Mapping[str, int]) -> str:
    canonical = json.dumps(sorted(bindings.items()), separators=(",", ":"))
    return f"v1:{sha256(canonical.encode()).hexdigest()}"
