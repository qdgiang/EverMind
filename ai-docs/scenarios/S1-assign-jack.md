# S1 — "Assign Jack": an authorized assignment in chat

> Verifies: chat write path, authority gate, supersession, projection refold, overload check,
> notifications. Traced against `design-v2.md` (2026-07-18). Gaps numbered globally G1–G6.

## Cast & canon (shared across S1–S5)

| Person | Role | Manager |
|---|---|---|
| An | Giám đốc (Director) | — |
| Joe | Trưởng phòng IT | An |
| Jack, Minh | IT members | Joe |
| Lan | Trưởng phòng Design | An |
| Hoa | Design member | Lan |

Project P-1 "Year-End Gala", `end_date 2026-11-30`. Canon from the two xlsx files: task **T-1**
"Mua 3 quả táo 1 đĩa hoa quả" (IT, status `todo`, start 11-12, end 11-13 17:00, budget note
300 USD) shaped by decisions D1–D6; **D6 (by Joe, effective) assigned Minh as PIC.**

## Scenario

2026-11-12 14:00, IT Telegram group, **Joe** types (plain prose, no marker):

> "Jack lo vụ mua hoa quả tuần này nhé."

## End-to-end trace (per design-v2 as written)

1. **Ingest** — one `messages` row (author resolved to Joe via `telegram_user_id`); the IT group's
   high-water counter ticks.
2. **Marker check** — no `!decision` → nothing fires per-message.
3. **Extraction** — at the next 100-message threshold, the window goes to the LLM in one call.
   Output: a decision {description ≈ "giao Jack mua hoa quả", payload = assignment change,
   `decided_by` = Joe (cited author), linkage → T-1, citation → the message}.
4. **Authority** — `can_decide(Joe, T-1)` = true (Joe above IT team) → **born `effective`**.
   One transaction: INSERT `decisions` (D7), `decision_tasks` (D7→T-1), `decision_citations`.
5. **Supersession** — Joe did not say "thay Minh" and cited no decision, so per the doc the system
   only *suggests* "supersedes D-6?" — no auto-flip. D6 (Minh) and D7 (Jack) are now **both
   effective assignment decisions on T-1**.
6. **Refold** — `task_assignments` recomputed from the fold. **Result is undefined** — see G1.
7. **Deadline rule** — no-op (T-1 already has an end date).
8. **Overload** — Jack's per-day load recomputes; if over threshold, a warning is raised —
   but only *after* the assignment already happened (see G4).
9. **Notification** — material change (PIC) → bot posts to the IT group tagging Joe, Jack
   (and Minh?), batched unless `urgent`.

**Subordinate fork:** if *Minh* had typed "để Jack làm đi" instead — identical through step 3, but
step 4 yields `proposed`: no projection change, Jack is NOT assigned, bot tags Joe to approve.
Only on approval do steps 5–9 run.

## What holds up ✅

- Attribution is verifiable (decided_by must be a cited author) — no forged authority.
- Append-only decision + citation chain: the assignment has a receipt.
- The subordinate fork correctly cannot mutate task state.
- Role snapshot (`decided_by_role_at_time`) keeps the trail honest if Joe changes roles later.

## Gaps

### G1 — Assignment payload has no add/replace semantics (severity: HIGH)
- **Current:** D6 {pic: Minh} and D7 {pic: Jack} are both `effective`. If payload means *set*,
  the fold is last-write-wins → **Minh silently dropped while D6 still reads `effective`** — a
  decision that is effective in status but contributes nothing, contradicting the lifecycle
  (status is supposed to track whether a decision is current). If payload means *add*, the fold
  is {Minh, Jack} — but then an intended replacement is impossible without explicit supersession.
- **Expected (your prefs):** review note "Một task có thể có nhiều PIC" (multi-PIC is normal), and
  your lifecycle rule "new decision → effective, flips the replaced one to superseded" — i.e. a
  shadowed decision must never stay `effective`.
- **Fix:** explicit ops in payload: `assign_add` / `assign_remove` / `assign_set`. Bare "giao X" →
  default **add** (non-destructive). `assign_set`/`remove` *require* a supersession link (system
  suggests, decider confirms via bot prompt). Invariant: no two effective decisions may set the
  same facet — enforced at the effective-write.

### G2 — `task_assignments`/`task_teams` look like writable tables (severity: LOW, doc clarity)
- **Current:** listed alongside real tables; doc also says the projection is never hand-edited.
- **Fix:** mark them explicitly as projection outputs — the only write is a decision containing an
  assignment op; joins are rebuilt by replay.

### G3 — Authority check is circular for task-creating decisions (severity: HIGH, cheap fix)
- **Current:** `can_decide(actor, task)` needs the task's team, but a `NEW_TASK` decision has no
  team until the decision itself sets one. Every task creation hits this.
- **Fix:** for `NEW_TASK` decisions, check authority against the **chat group's team** (via
  `chat_groups.team_id`); dashboard creations check against the team picked in the form.

### G4 — No pre-assignment overload gate in chat (severity: MEDIUM)
- **Current:** "warn before assigning, log the override" exists only on the dashboard. In chat the
  decision is already effective before the load check runs; "override logged" is undefined because
  the assigner never saw a prompt.
- **Expected:** warn-don't-block with the override recorded (your resolution of open question 2).
- **Fix:** define chat semantics: post-hoc warning reply tagging Joe + Jack ("Jack now has N tasks,
  M due this week"); no retraction within X hours = implicit acceptance, noted on D7.

### G5 — Pending proposals are invisible in chat (severity: MEDIUM)
- **Current:** the subordinate fork creates `proposed` and tags the approver — but nothing tells
  the *group* that Jack is NOT yet assigned. Everyone who read Minh's message assumes he is.
- **Fix:** bot always replies to proposal-generating messages with an explicit state marker:
  "📋 Proposed: assign Jack → T-1 — awaiting @Joe". Approval/rejection edits or follows up.

### G6 — Assignment vs status are orthogonal; unstated (severity: LOW, doc clarity)
- **Current/Fix:** state explicitly: assigning Jack does NOT move `todo → doing` (only a PIC
  `task_update` does), and assignment is NEVER a `task_update` — always a decision.

## Verdict

The spine works: message → cited decision → authority gate → fold → notify. The break point is
**facet semantics** (G1): without add/remove/set ops the fold is ambiguous exactly where the
review is most explicit (multi-PIC), and the effective-but-shadowed state violates the decision
lifecycle you specified.
