# S2 — "Jack completes it": progress reported in plain chat

> Verifies: PIC progress path (`task_updates`), extraction targets, lamps (overdue/stale), digest
> truthfulness, dependency unblock ping. Traced against `design-v2.md` (2026-07-18). Gaps G7–G9.
> Cast & canon: see S1. Precondition: S1 resolved with G1's fix → T-1 PICs = {Minh, Jack}.

## Scenario

2026-11-13 16:40 (T-1 is due today 17:00), IT group, **Jack** types (plain prose, no marker):

> "Mua xong hết rồi nhé — 3 táo + 1 đĩa, hết 280 USD."

At 16:40 the IT group sits at message ~137 of its current extraction window (101–200).

## End-to-end trace (per design-v2 as written)

1. **Ingest** — `messages` row (author = Jack). Counter at 137 — **threshold not reached; no AI
   pass runs.**
2. **Marker check** — no `!progress` → nothing fires.
3. **17:00 passes** — T-1's projection still says `todo`. The `overdue` lamp derives ON. Any radar
   sweep or digest generated tonight reports T-1 overdue — *chat already knows it's done; the
   system doesn't.*
4. **Next day ~11:00, message 200 arrives** — extraction fires on window 101–200. The LLM sees
   Jack's completion. Now the doc's stated targets are: *decisions + weak signals (blocker-ish,
   dependency-ish)*. A completion is neither. And `task_updates.created_from` allows only
   `marker|dashboard`. So, as written, one of three wrong things happens:
   - **(a) dropped** — not a decision, not a listed weak signal → T-1 stays `todo` forever until
     someone uses the dashboard or a marker;
   - **(b) mis-typed as a decision** — Jack is not authorized → born `proposed`, and **Joe must
     approve that Jack finished his own task**, directly violating the review's carve-out ("trừ
     việc PIC cập nhật tiến độ task");
   - **(c) treated as an unknown weak signal** → triage inbox, same practical effect as (a).
5. **What should follow — but can't yet:** status → `done`; Jack's load drops; any task depending
   on T-1 gets the "unblocked, you can start" ping; the weekly digest lists T-1 under completed.

## What holds up ✅

- The marker fast path is fine: `!progress T-1 done` at 16:40 would apply instantly (Jack is PIC),
  lamps never misfire, dependents get pinged same-minute.
- Dashboard path is fine: Jack flips status → `task_update`, no approval, correctly scoped.
- The projection/fold handles completion cleanly once an update exists (status is a task_update
  facet; no supersession machinery involved — correct, per your "PIC progress is separate" rule).

## Gaps

### G7 — Plain-chat progress has NO path into the system (severity: BLOCKER)
- **Current:** extraction emits only decisions; `task_updates.created_from ∈ {marker, dashboard}`.
  A PIC saying "done" in chat — the single most common coordination message that exists — is
  dropped or, worse, routed into an approval queue (4b).
- **Expected (your prefs):** the review's explicit carve-out (PIC updates progress without
  approval) + the ambient-capture ethos (zero new habits — nobody should need a marker to say
  "done") + your batch-flow description ("crawl 100 → AI gets what happened for the tasks").
- **Fix:** extraction emits **proposed `task_updates`** alongside proposed decisions. Add `llm` to
  `created_from` + a `confidence` field + `source_message_id` citation. Auto-apply iff the cited
  author is a PIC of the linked task; otherwise it needs an ack (see G9). Progress updates never
  enter the decision approval queue.

### G8 — Batch latency makes lamps/digest lie (severity: HIGH)
- **Current:** between "done" in chat (16:40) and the next threshold crossing (next day), the
  projection is stale: overdue lamp ON, radar would ping, a digest generated in that window
  reports falsehoods. v1's own warning applies: false pings erode trust fast.
- **Expected:** receipts-grade truthfulness — the system must never *assert* something chat
  already contradicts.
- **Fix (two cheap layers):** (1) **flush-before-read**: digest generation and radar sweeps force-
  extract each group's partial window first (same mechanism as the replay-end flush); (2) promote
  the marker path in onboarding as the instant lane for time-sensitive updates. Optionally stamp
  digest lines with "as of message #N".

### G9 — Who may report completion is undefined for non-PICs (severity: MEDIUM)
- **Current:** with G7's fix, auto-apply is PIC-only. But Joe saying "Jack bảo xong rồi" (not a
  PIC) or a teammate relaying it has no defined handling.
- **Expected:** review scopes progress edits to the PIC; authority can do anything via decisions.
- **Fix:** three lanes, by author: **PIC** → auto-apply; **authority over the task** → apply as a
  decision-grade status change (they outrank the carve-out); **anyone else** → bot asks a PIC to
  confirm with one tap (👍 on the bot's reply applies it, attributed to the confirming PIC).

## Verdict

The completion path is the weakest subsystem in v2: the one message type every volunteer sends
("done") currently has no ambient route into the model (G7), and threshold-batching means the
system can briefly assert the opposite of what the whole group just read (G8). Both fixes are
small and don't disturb the decision lifecycle; G7 should land before schemas freeze because it
changes `task_updates`' shape.
