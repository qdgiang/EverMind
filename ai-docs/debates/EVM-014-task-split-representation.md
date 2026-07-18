# EVM-014 — Decide how task split is represented

> Priority: P1 · Status: `OPEN`

## Problem

Rev 9 says split is composed from child creation and parent refinement, while UI scenarios offer a
one-tap split. No relation currently tells projections or reasoning views which children belong to
the split.

## Options

- **Option A — Generic task-relation graph:** flexible but speculative for one decomposition use case.
- **Option B — Nullable `parent_task_id`:** smallest honest representation if split remains in MVP.
- **Option C — Defer one-tap split (`PROPOSED` when not required by the hero demo):** allow manual child
  tasks and avoid promising a flow the model cannot explain.

## Acceptance criteria

- MVP explicitly chooses B or C; it does not claim split without a representation.
- If B is chosen, child creation and parent linkage are atomic/auditable.
- Parent status is not silently derived from children without a separate approved rule.
- Merge and transfer preserve or deliberately revalidate parent linkage.
