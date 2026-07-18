# S12 — Can the Monday digest match what mai and linh already write by hand?

> Verifies: v2's "digest computed from decisions + updates" against the corpus's 15 planted
> weekly wraps — the ground truth for what a *good* status summary contains. Cast/canon: `data/`
> corpus. Gaps G34–G35. Complexity: ★★★★☆.

## Grounding (answer key: statuses; esp. S-w26-events m0303, S-w28-events m0500)

v2 killed status *extraction* (settled decision #5) on the theory that the digest can be
**computed**. The corpus lets us test that theory: real leads wrote real wraps. S-w26-events
(m0303): *"Venue = Nguyen Du gym, signed; 14 committed stalls + 3 new inquiries; volunteers
26/30; stall map v2 done; t-shirt and poster final. Open items: sound quote, banner printing
quote."*

## Trace — generate the W26 events digest from v2 data, diff against m0303

| Wrap line (human) | v2-computable? | From |
|---|---|---|
| Venue = Nguyen Du gym, signed | ✅ | D2 + venue task done-update |
| Open: sound quote | ✅ *only if* S8-G27 ledger built | B1 signals |
| T-shirt final | ✅ | D6 (marker) |
| Stall map v2 done | ⚠️ only if "stall map" ever materialized as a task | linkage-dependent |
| **14 committed stalls + 3 inquiries** | ❌ no entity can hold this | — |
| **Volunteers 26/30** | ❌ | — |
| Poster final | ⚠️ same as stall map | — |

Verdict of the diff: the *decision/blocker skeleton* computes, but the wrap's most
informative lines are **aggregate metrics** (counts against targets: stalls, volunteers, budget
%). S-w27-comms even reports "budget at ~82% of the all-hands cap" — a metric *derived from a
policy* (TD2's 25M cap). v2 has no place for any of it: not a task facet, not a decision, not a
blocker. The computed digest would be *correct but thinner than what the team already had for
free* — a regression the audience will feel instantly if a judge compares.

Second finding: the wraps themselves (m0303, m0500…) are natural-language summaries **rich in
citations-worthy content**, posted by exactly the right person (the lead). Under v2 they extract
to… nothing (not decisions, not progress on a single task). The system discards the best
summary-shaped signal in the corpus.

Third finding, small: **X3** (parking fee — "postponed", never revisited) and **X4** (snack
vote postponed). Correctly extracted to nothing today; but real groups *lose* these, and the
corpus planted them as recognizable real-world debris.

## What holds up ✅

- The skeleton computes: decisions-this-week (with receipts), completed tasks, open/new blockers,
  pending proposals — all real digest lines from real data. Killing status *extraction* was still
  right: nobody should have to write wraps for the system's benefit.
- Precision on X3/X4: no phantom records. Correct.

## Gaps

### G34 — Metrics and lead-wraps have no home; the digest computes thinner than the hand-made
### original (severity: MEDIUM-HIGH)
- **Expected:** the digest's bar is m0303 — beat the manual wrap, or at least tie it.
- **Fix (two cheap layers, no metrics engine):**
  1. **Team-scoped notes** (rides on S7-G26 scope): when a lead posts a wrap-shaped message,
     extraction captures it as a team-scoped note update with citation. The digest *quotes* the
     freshest team note verbatim, attributed and cited, alongside the computed skeleton. The
     human's numbers ride along without the system modeling them.
  2. **Named counters (stretch, honest scope):** `counters {team, name, value, target?, ts,
     source_msg}` — extraction updates them from statements like "volunteers 26/30" as
     append-only points. Digest renders latest value + trend arrow. No formulas, no rollups —
     a labeled number with a receipt. Only build if time remains; layer 1 alone closes the
     felt gap.

### G35 — Parked topics evaporate (severity: LOW, optional)
- **Fix:** when extraction sees an explicit deferral ("để sau", "postpone", "chưa chốt, tuần sau
  bàn tiếp"), record a signal (S8-G27 ledger, `kind: parked`) — surfaced in the digest as
  "parked, no owner: parking fee (since 07-02)" after N quiet days. Strictly explicit-deferral
  language only; X-grade distractors must not resurrect as noise.

## Verdict

Settled decision #5 survives — but only with G34.1: the computed digest needs to *carry* the
human wrap, not compete with it. The corpus's planted statuses turn out to be the spec for the
digest's quality bar, and pure decision/blocker computation clears barely half of it.
