# S6 — The t-shirt order: a real task lifecycle across two channels

> Verifies: decision→task materialization, marker path on real (v1-style) markers, blocked-on-an-
> external-party, cross-channel task identity, in-chat delegation. **First corpus-grounded
> scenario: cast/canon = `data/` synthetic corpus (AIV NPO), which is authoritative for the demo.**
> S1–S5 used a fictional cast from the xlsx; note the name collision — corpus `an` is a comms
> *member*, not a director. Gaps G22–G25. Complexity: ★☆☆☆☆ (but 4 gaps — richest storyline).

## Grounding (answer key: D6, B4)

- Quote debate + chốt: `aiv-comms`, 06-30. **m0337 (phuong, comms lead): "any objections? nếu
  không thì minh chốt luôn nhé" is the comms channel's message #100** — the C1 window boundary.
- **m0338 (minh): `!decision fair t-shirts: going with InTheXanh, 120 shirts, navy…` is comms
  #101** — first message of the flush-only tail (comms has 156 messages; no second window fires).
- **m0447 (minh), `aiv-events` #181, window E2:** `!blocked — InTheXanh vừa báo máy in lỗi… CHƯA
  có ETA mới… Ảnh hưởng: áo volunteer + áo bán ở fair.`
- Answer key: D6 team=**comms**; B4 team=**events**. Same real-world workstream, two teams.

## Trace (v2 as written)

1. **m0338 marker fires per-message** — instantly, which *rescues* D6 from the C1 boundary (the
   passive path would not see comms #101+ until final flush). Score one for the marker lane.
2. But the marker is **v1-style: no task ref**. v2's marker grammar is `!decision T-12 …`; bare
   markers have no defined linkage → NEW_TASK? UNLINKED? Undefined (G24). Assume NEW_TASK: task
   **T-shirt order** created, team=comms (the group's team), PIC…unset (nobody said who).
3. **Authority:** minh is a *member* (design), not a lead. Under `can_decide`, m0338 is born
   **`proposed`** — despite phuong (comms lead) having said, one message earlier, "nếu không thì
   minh chốt luôn nhé" (= go ahead and lock it). The answer key says this IS a decision, decided
   by minh. v2 has no concept of delegation (G25) → the corpus's own ground truth comes out
   `proposed` in v2. **The eval would score this extraction wrong through no fault of the LLM.**
4. **m0447 (`!blocked`, events window E2):** marker fires; again no task ref (G24). The events
   group's team is *events* — the linkage candidates are **events tasks**, and the t-shirt task
   created in step 2 is a **comms** task. The extractor cannot see it → creates a second task
   (or lands UNLINKED). **One real workstream, two team-scoped task rows** (G23) — and the answer
   key itself split the pair across teams, so this is not a corpus bug; it's reality.
5. **The blocked state:** minh's message carries `waiting_on` (InTheXanh's new ETA), an implicit
   `since` (07-07), an owner (minh), and impact scope. v2's `status=blocked` + free-text note is
   all that survives — v1's `BlockerBody {waiting_on, owner, since}` was structurally **lost** in
   the v2 pivot (G22). The radar can compute "blocked for N days" only if `since` exists.

## What holds up ✅

- Marker-at-ingest saved the decision from a window boundary — the deterministic lane earning its
  keep on real data, exactly as designed.
- linh's reply m0448 ("nếu thứ 6 vẫn chưa có ETA thì mình tìm xưởng khác") is a conditional
  future decision — correctly NOT extractable as a decision now; precision rules hold.
- Citations: D6/B4 each anchor to a single clear message; receipts work.

## Gaps

### G22 — External-wait blockers lost structure in the v2 pivot (severity: HIGH)
Every planted blocker in the corpus (B1 vendor, B2 chi Yen, B3 school IT, B4 InTheXanh, B5 chi
Yen) waits on a party **outside the task graph**. v2's dependency lamps (task→task) fire for none
of them; `status=blocked` + note is lossy. **Fix:** blocked state carries structured fields again:
`waiting_on (text), since (date), owner (user)` — set by the blocking update/decision; staleness
radar keys off `since`; digest groups blockers by `waiting_on`.

### G23 — One real task, two team-scoped identities (severity: HIGH)
Linkage candidates are scoped to the group's team, so cross-channel workstreams split into
duplicate tasks (t-shirts: decided in comms, blocked in events). Dedup can't save it — the
candidates never met. **Fix:** candidates = the **project's** open tasks (10² scale — trivially
fits a prompt), with the group's team's tasks listed first; `task_teams` already models the
multi-team ownership once linked.

### G24 — Bare markers (the corpus's markers!) have undefined linkage (severity: MEDIUM)
All 7 marked corpus messages are v1-style, no `T-…` ref. **Fix:** define bare-marker behavior:
record created instantly (deterministic), then linkage resolved like any extraction (candidates,
`NEW_TASK` fallback, UNLINKED→triage); the marker's *record creation* stays non-AI, only its
*task attachment* may use the linker. Corpus-rework: add task refs to some planted markers so
both forms are tested.

### G25 — Delegation-in-chat is unrepresentable (severity: MEDIUM)
"Nếu không thì minh chốt luôn nhé" is an authority delegating one decision — utterly ordinary in
real groups. v2's gate would still hold minh's decision `proposed`. **Fix (cheap):** approval by
prior utterance — if an authorized user's cited message in the same thread/window explicitly
authorizes the maker ("chốt đi", "you decide"), extraction sets `approved_by` to them and the
decision is born effective with *both* messages cited. (General delegation grants = roadmap.)

## Verdict

The corpus's cleanest task story exposes that v2's *edges* are team-shaped where reality is
project-shaped (G23), and that v2 threw away blocker structure v1 already had (G22). The marker
lane performs; the authority gate misfires on a legitimate, delegated, ground-truth decision.
