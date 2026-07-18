# EVM-021 — Prevent stale dashboard writes from overwriting chat state

> Priority: P0 · Status: `OPEN`

## Problem

A dashboard form can be opened from an old projection while a chat decision changes the same
facet. Submitting the stale form must not silently supersede newer context.

## Options

- **Option A — Last submitted write wins:** familiar but unsafe and hides cross-surface conflict.
- **Option B — Optimistic command versioning (`PROPOSED`):** include expected resource/facet version and
  client command ID; show a diff and require reconfirmation on mismatch.
- **Option C — Lock resources while edited:** prevents conflict but is brittle for asynchronous chat and
  long-lived browser sessions.

## Acceptance criteria

- A stale dashboard command cannot overwrite a newer facet without explicit reconfirmation.
- Double-click/retry with one command ID produces one domain event.
- The accepted command still passes current authorization and terminal-state checks.
- Successful writes use domain event → projection → outbox; they are never fake-ingested messages.
