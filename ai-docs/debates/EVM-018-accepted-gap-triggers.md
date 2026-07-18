# EVM-018 — Keep G61/G64 accepted with revisit triggers

> Priority: P2 · Status: `ACCEPTED`

## Problem

Peer-lead decision churn (G61) and an explicit negotiation lifecycle state (G64) are real gaps, but
their fixes add tuned alerts and lifecycle/UI branches under the hackathon clock.

## Options

- **Option A — Implement both now:** closes the gaps but expands scope before core contracts exist.
- **Option B — Accept with observable triggers (`PREFERRED`):** keep documented workarounds and queries;
  revisit when real usage crosses an agreed threshold.
- **Option C — Remove the affected flows:** reduces scope but weakens honest proposal and peer-authority
  behavior.

## Acceptance criteria

- Both accepted gaps remain named in the spec and issue catalog.
- A query/runbook can identify repeated peer flips and stale negotiated proposals.
- Revisit thresholds and responsible owner are recorded before production rollout.
- Workarounds never present pending negotiation or peer churn as resolved truth.
