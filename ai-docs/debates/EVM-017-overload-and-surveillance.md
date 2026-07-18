# EVM-017 — Bound overload warnings without surveillance

> Priority: P2 · Status: `OPEN`

## Problem

Cross-team workload can reveal bottlenecks, but person-centric ranking or leaking inaccessible task
details can damage trust and violate project-scoped visibility.

## Options

- **Option A — Person productivity leaderboard:** easy to compare, harmful and not evidence of capacity.
- **Option B — Explainable workload-risk warning (`PROPOSED`):** warn rather than block, expose the input
  formula, allow correction, and aggregate hidden-project load without titles.
- **Option C — Remove person-level overload:** avoids surveillance but loses a real coordination signal.

## Acceptance criteria

- No productivity ranking or performance score is shown.
- Assigner and assignee can inspect/correct accessible inputs.
- Inaccessible project work contributes only an aggregate risk indicator.
- Warnings are advisory, attributable, and do not silently block assignment.
