# EVM-015 — Define evidence retention, deletion, and redaction

> Priority: P0 · Status: `OPEN`

## Problem

EverMind caches source revisions as receipts, but delete signals, retention, consent, redaction,
and access to cached copies are not a complete policy. Confirmed truth and raw evidence have
different retention needs.

## Options

- **Option A — Retain raw evidence forever:** strongest audit with unacceptable privacy/storage risk.
- **Option B — Configurable retention plus tombstone/redaction (`PROPOSED`):** preserve audit metadata
  and derived decisions while governing raw text/file access separately.
- **Option C — Delete all derived records with source deletion:** privacy-simple but destroys institutional
  memory and decision accountability.

## Acceptance criteria

- Policy distinguishes raw source, revisions, confirmed records, and audit metadata.
- Delete/redaction events are auditable and authorization-checked.
- A surviving decision shows `source unavailable/redacted` rather than fabricating a receipt.
- Cached-copy access follows explicit scope and retention policy.
