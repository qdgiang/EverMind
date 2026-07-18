# S15 — Full-corpus replay audit: v2-as-designed, scored against the answer key

> The capstone: replay all 532 messages + the transcript through the v2 pipeline exactly as
> `design-v2.md` specifies, with the real per-channel window math, and score coverage against
> `answer_key.json`. Gaps G39–G40 (plus the scorecard, which references the whole register).
> Complexity: ★★★★★.

## The window map (counted, batch = 100 per group)

| Channel | Msgs | Windows that fire mid-replay | Flush-only tail |
|---|---|---|---|
| aiv-events | 216 | E1 (#1–100, ends **m0250** — mid-venue-thread), E2 (#101–200) | #201–216 |
| aiv-education | 160 | Ed1 (#1–100, ends ~m0330) | #101–160 — **includes D4 (m0358)** |
| aiv-comms | 156 | C1 (#1–100, ends **m0337** — one msg before D6) | #101–156 — incl. B2-resolution (m0370) |
| meeting/06-28 | 88 | **none** (88 < 100) | everything (TD1, TD2, TB1) |

**4 AI passes** during the whole 5-week replay; everything else waits for a terminal flush.
Markers fire per-message throughout (D3, D6, D8, B2, B4 rescued instantly).

## Scorecard — v2 as designed today (no scenario fixes applied)

| Planted | Outcome | Why |
|---|---|---|
| D1 venue #1 | ✅ E1 | clean extraction |
| D2 venue #2 | ⚠️ E2, **citations fail** (m0245/m0248 unciteable) | S9-G28 |
| D3 classes Sat (marker) | ✅ instant | marker lane |
| D4 classes → Sunday | ⚠️ extracted only at **final flush** | flush-only tail |
| D5 VietQR | ❌ UNLINKED → triage (policy, no task) | S7-G26 |
| D6 t-shirts (marker) | ⚠️ instant but `proposed` (minh not authorized; delegation invisible) + duplicate-task risk | S6-G25/G23 |
| D7 buddy system | ❌ UNLINKED (policy) | S7-G26 |
| D8 free entry (marker) | ⚠️ instant but UNLINKED-shaped (policy) | S7-G26 |
| B1 sound vendor (implicit, 3 mentions E1/E2/E2) | ❌ **missed** — sub-threshold per window | S8-G27 |
| B2 e-banking (marker) | ⚠️ opens instantly; **resolution never lands mid-replay** (m0370 in tail; plain chat) | S2-G7/G8 |
| B3 projector | ⚠️ Ed1, single window — extractable, external-wait fields lost | S6-G22 |
| B4 printing (marker) | ⚠️ instant; linkage/team split | S6-G23/G24 |
| B5 FB access | ⚠️ C1; waiting-on-chi-Yen is a string | S11-G32 |
| TD1 fair **date** / TD2 budget **cap** / TB1 **permit** | ❌❌❌ **never extracted** | S10-G29 |
| 15 weekly wraps | invisible to digest (by design #5, unmitigated) | S12-G34 |
| Hero Q&A #1 venue | ⚠️ answerable, receipts incomplete | S9-G28 |
| Hero Q&A #2 Sunday | ⚠️ answerable only after final flush | timing |
| Hero Q&A #3 donations | ❌ unanswerable | S7-G26 |

**Net: 2 clean of 11 decisions; 1 of 3 hero Q&A beats fully works; the fair's date, budget cap,
and biggest risk never enter the system.** The pipeline is *sound* on task-shaped, single-window,
authorized, chat-native events — and the corpus was deliberately built to be messier than that.
With the register's fixes applied (G22–G38), every row above upgrades to ✅ except the metrics
lines (G34.2 optional): projected **full answer-key coverage**.

## Two audit-specific gaps

### G39 — Demo pacing: batch=100 makes the replay a 4-beat show + a giant finale (severity:
### MEDIUM, config-only)
Live audiences should watch records materialize *throughout* the replay. `EXTRACTION_BATCH_SIZE`
is already env-config: **run the demo at ~25** (→ ~21 windows, extraction every few on-screen
minutes) and eval/CI at 100 (production shape). One env var, two profiles — document in the demo
runbook so nobody "fixes" the mismatch on stage.

### G40 — The golden set's windows are not production windows (severity: HIGH for the eval gate)
`golden_set.json` = 21 hand-picked slices of **8–20 messages**; production windows are ~100. The
eval gate would measure a shape the pipeline never runs — precision on 15-message windows says
little about 100-message windows (more distractors per call, linkage across more topics).
**Fix:** relabel the golden set as the corpus's *actual* windows (deterministic: same corpus +
same N → same windows, incl. the flush tails and the transcript-as-one-window). Keep a handful of
small slices as unit-grade cases; the gate runs on production shape.

## Verdict — the question you asked

**Do projects, decisions, and tasks as currently set up correctly model the real world (as your
own synthetic data defines it)?** The *core* does: append-only decisions with supersession, tasks
as folds, citations as receipts survived every scenario untouched — S9 proved the hardest
mechanic (mid-thread boundary supersession) works. What does not survive contact is the
*assumption layer* around that core: that every decision has a task (S7), every blocker has a
predecessor task (S6), every signal fits one window (S8), every source reaches 100 messages
(S10), every person is a current user (S11), every member has one team and every org a root
(S13), and every workstream has an end date (S14). Each assumption is contradicted by planted,
hand-verified ground truth. The good news: all of it is fixable at the seams — scope, ledger,
flush rules, join tables, one column — with the decision lifecycle you specified left exactly
as it is.
