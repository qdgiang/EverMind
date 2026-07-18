# S7 — "Donations via VietQR": the decision that has no task

> Verifies: whether v2's decisions-must-link-to-tasks model fits the decisions the corpus actually
> plants. Cast/canon: `data/` corpus. Gap G26. Complexity: ★★☆☆☆ — one gap, but a **blocker**.

## Grounding (answer key: D5, D7, D8; also TD2)

- **D5** (comms, 06-17, m0148/m0150): donations via VietQR bank transfer, not Momo — chosen for
  traceability. *Hero Q&A question #3 depends on it.*
- **D7** (education, 06-19, m0180): buddy system — every new volunteer paired with a mentor.
- **D8** (events, 07-08, m0465, `!decision`): fair entry FREE + donation box, replacing the 20k
  ticket idea (which was only ever floated — distractor X2, never decided).
- **TD2** (transcript): budget cap 25M VND, overrun requires linh's sign-off, prizes cut first.

## Trace (v2 as written)

1. Extraction (or the marker, for D8) produces the decision with citations — that part is fine.
2. **Linkage:** the LLM must return `task_id | NEW_TASK | UNLINKED`. What task is "how donations
   work"? There is no donations task — D5 is a **policy**. Same for D7 (a process rule), D8 (an
   event format rule), TD2 (a budget policy + an approval rule). Honest linkage answer: UNLINKED.
3. **UNLINKED → triage inbox** per design. So **5 of the 8+3 planted decisions (D5, D7, D8, TD2,
   and arguably D3/D4 — the class schedule is a recurring-program policy, not a task facet) land
   in a human triage queue** and never reach the projection, the digest, or Q&A.
4. Consequence chain: the digest's "decisions this week" misses most planted decisions; the
   reasoning popup never sees them (no task); and **hero Q&A #3 ("How do people donate, and
   why?") cannot be answered** — its expected keys (D5) exist only in an inbox.

## What holds up ✅

- Task-shaped decisions (venue booking, t-shirt order) fit the model perfectly — the failure is
  selective, which is what makes it diagnosable.
- The append/supersede lifecycle is *right* for policies too: a future "switch to Momo" should
  supersede D5 exactly like venue moves supersede venues. The lifecycle needs no change — only
  the mandatory task link does.
- X2 (20k ticket, floated, no conclusion) correctly extracts to nothing; D8's rationale can still
  *mention* replacing the floated idea without a supersession link (nothing effective existed).
  Precision semantics hold.

## Gaps

### G26 — Decisions require a task; half the real ones don't have one (severity: BLOCKER)
- **Current:** `decision_tasks` ≥ 1 in spirit; UNLINKED = triage. The corpus proves most
  institutional-memory decisions are **scope-level**: how we take money, how we onboard, what
  entry costs, what the budget cap is. This is the original v1 insight (decisions as memory) that
  the v2 task-pivot accidentally amputated.
- **Expected (your prefs + the data):** the review's decision log has "Task affected" — but its
  own Note field says "impact of the decision", and the answer key's Q&A beats *require*
  policy decisions to be first-class and retrievable.
- **Fix:** decisions get a **scope**: `task(s) | team | project`. `decision_tasks` stays for
  task-scoped ones; team/project-scoped decisions link to their team/project instead. Extraction
  linkage returns `task_id | NEW_TASK | TEAM_POLICY | PROJECT_POLICY` (UNLINKED remains only for
  genuinely unplaceable output). Digest gains a "policies decided" line; Q&A retrieves by scope;
  supersession works per topic within a scope (VietQR ↔ Momo). The reasoning popup equivalent for
  a team/project is the existing decision-log view filtered to that scope — no new UI.
- **Bonus:** TD2's "overrun requires linh sign-off" shows policies can carry *rules*. v2 does not
  execute rules — store them as policy text, surfaced when relevant (roadmap: rule engine — out
  of 48h scope, say so).

## Verdict

As designed, v2 would fail its own answer key on the majority of planted decisions and break a
hero demo beat. One schema addition (decision scope) restores the entire v1 memory story inside
the v2 task model — this is the single highest-leverage fix in the batch.
