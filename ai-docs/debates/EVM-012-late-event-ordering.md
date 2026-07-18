# EVM-012 — Define deterministic late-event ordering

> Priority: P1 · Status: `OPEN`

## Problem

Transcripts, imports, delayed webhooks, and retries can arrive out of order. Arrival order can
rewrite present truth with older history, while equal timestamps make replay nondeterministic.

## Options

- **Option A — Arrival order:** operationally simple but historically incorrect.
- **Option B — Valid causality, then total event order (`PROPOSED`):** honor valid causal links, otherwise
  order by `event_ts → recorded_at → stable_event_id`; old events enter history without rewind.
- **Option C — Full bi-temporal model:** strongest query semantics but defer until current replay needs
  prove insufficient.

## Acceptance criteria

- Late older history does not change the current projection.
- Equal event timestamps replay deterministically.
- An explicit supersession with impossible chronology goes to triage.
- Views expose event and recorded timestamps when they differ.
