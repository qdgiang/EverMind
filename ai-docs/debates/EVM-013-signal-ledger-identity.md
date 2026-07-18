# EVM-013 — Prevent false signal-ledger merges

> Priority: P1 · Status: `OPEN`

## Problem

Free-text topic matching can merge unrelated risks across projects, tasks, or similarly named
external parties. A false merge can create or resolve the wrong blocker.

## Options

- **Option A — Global free-text topics:** minimal schema with high false-merge risk.
- **Option B — Scoped structured identity (`PROPOSED`):** key by project, task when known, party, and
  normalized topic; confirm the first party match and audit merge/split corrections.
- **Option C — Fully automatic embedding clusters:** useful discovery but too probabilistic to own domain
  identity without human correction.

## Acceptance criteria

- Same words in different projects do not merge by default.
- A first fuzzy party match requires confirmation.
- Merge/split keeps all source citations and correction events.
- Signal contradiction cannot resolve a human-asserted blocker; PIC/authority action is required.
