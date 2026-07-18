# S3 — "I'll buy apples" → Joe overrules: "buy peaches"

> Verifies: proposal lifecycle, supersession authority, overrule narrative, PIC autonomy boundary.
> Traced against `design-v2.md` (2026-07-18). Gaps G10–G13.
> Cast & canon: see S1. Standing state: **D5 "mua 3 quả táo" was decided by An (Giám đốc)** and is
> `effective` on T-1. Jack is a PIC of T-1.

## Scenario

IT group, 2026-11-12:

> 09:00 **Jack:** "Mai tôi đi mua, chắc mua táo xanh cho đẹp."
> 14:00 **Joe:** "Thôi, đổi sang mua đào đi — khách thích đào hơn."

## End-to-end trace (per design-v2 as written)

1. **Ingest ×2** — two `messages` rows; no markers fire.
2. **Extraction (both in the same window)** — the LLM returns two candidate decisions linked to
   T-1:
   - **D7** from Jack's message: {description ≈ "mua táo xanh", decided_by = Jack}.
   - **D8** from Joe's message: {description ≈ "đổi sang mua đào", decided_by = Joe}, and — same
     task, same facet ("what to buy"), no explicit ref — the system raises a **"supersedes D-5?"
     suggestion** rather than auto-flipping.
3. **Authority, D7** — Jack is a PIC, not in the manager chain above IT → **born `proposed`**.
   Projection untouched. Bot tags Joe to approve (and, per S1-G5's fix, announces the pending
   state to the group).
4. **Authority, D8** — `can_decide(Joe, T-1)` = true → **born `effective`**. Joe confirms the
   supersession suggestion → one transaction: D8 effective, `D8.supersedes = D5`,
   **D5 → `superseded`** with back-pointer.
5. **Refold** — T-1's description facet now folds from D8: peaches. Notification tags Joe, the
   PICs (Jack, Minh), citing D8.
6. **Leftover** — D7 still sits `proposed`, tagging Joe for approval of a plan that is now moot.

## What holds up ✅

- Jack's intent correctly cannot mutate the task (born `proposed`; projection untouched).
- The supersession write itself is exactly your append + status-update semantics: D8's body
  immutable, D5's body untouched, only D5's status flipped, links in both directions.
- The suggestion-not-auto-flip rule prevented a silent burial: a human (Joe) confirmed the link.
- Reasoning popup: apples → peaches shows up as two decisions with receipts, superseded hidden by
  default, unhide toggle reveals D5 — the review's requirement, working.

## Gaps

### G10 — Joe just overrode the Director, and the model allowed it (severity: BLOCKER)
- **Current:** `can_decide(actor, task)` checks only *task scope* (actor above the task's team).
  D5 was made by **An (Giám đốc)**. Joe sits *below* An, yet his D8 superseded An's decision with
  no escalation, no approval, not even a notification to An.
- **Expected (your prefs):** review §III, rule 1 — "cấp dưới không thể ảnh hưởng đến quyết định
  của người có cấp bậc cao hơn"; a lower rank may *propose* against a superior's decision, but it
  becomes effective only when someone with sufficient rank approves.
- **Fix:** supersession has its own gate: to supersede decision `D_old`, require
  `rank(actor) ≥ rank(D_old.decided_by_role_at_time)` (compared via the manager chain / role
  ladder). Fails → the new decision is born `proposed` and the bot tags the original maker (or
  the nearest sufficient authority) to approve. Note the snapshot field is what makes this
  checkable even after role changes — it was already in the schema, now it has a consumer.

### G11 — Zombie proposals: D7 pends forever on a dead facet (severity: MEDIUM-HIGH)
- **Current:** nothing resolves `proposed` decisions when a later effective decision lands on the
  same task + facet. Joe stays tagged to approve "green apples" after deciding peaches; the
  approval queue accumulates rot and the bot nags about corpses.
- **Expected:** an approval queue that only contains live questions.
- **Fix:** the effective-write transaction also sweeps `proposed` decisions on the same
  task + facet → status `rejected` (reason: overruled), link them to the winning decision (G12),
  and notify their authors ("your proposal was overruled by D8").

### G12 — The story "Joe overruled Jack" is unrepresentable (severity: MEDIUM)
- **Current:** D7 (proposed/rejected) has no link to D8. The reasoning popup can show *that*
  peaches won, but not that Jack's plan existed and was overruled — yet "decisions must not be
  re-explained" and the popup's job is the *why*, per the review.
- **Fix:** reuse the existing pointer: set `D7.superseded_by_decision_id = D8` when the sweep in
  G11 resolves it (status stays `rejected`, so lifecycle semantics stay clean). Popup renders it
  as "overruled by D8". Zero new columns.

### G13 — Was Jack's message even a decision? PIC autonomy is unbounded (severity: HIGH for trust)
- **Current:** every PIC musing about *how* they'll execute ("green ones, for looks" — consistent
  with D5's "3 apples") becomes a `proposed` decision tagging Joe. Ten volunteers thinking out
  loud = an approval-spam queue. This is the v2 shape of the false-positive problem: precision
  failure moved from extraction into *workflow*.
- **Expected:** review's carve-out gives PICs an execution zone; the reasoning popup wants such
  context captured as **notes**, not authority events.
- **Fix:** extraction rule — a PIC statement about their own task that does not *contradict* any
  effective decision on it → captured as a `task_update {kind: note}` (via S2-G7's llm-sourced
  updates), auto-applied, shown in the popup's context. Only contradiction or scope change
  escalates to a `proposed` decision. (Jack's "táo xanh" = note; had he said "mua lê thay táo",
  that contradicts D5 → proposed decision.)

## Verdict

Your example scenario is the most valuable of the five: the mechanics of append + status-flip
work exactly as you specified (D5's burial is clean, auditable, reversible), but **authority is
only half-modeled** — it gates *who may decide about a task* while ignoring *whose decision is
being displaced* (G10), and the boundary between a PIC executing and a PIC deciding (G13)
determines whether the approval queue is signal or spam.
