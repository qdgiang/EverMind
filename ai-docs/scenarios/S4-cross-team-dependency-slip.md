# S4 — Design slips, IT is blocked: a cross-team dependency under stress

> Verifies: dependency edges, derived lamps, escalation routing, visibility carve-out, weak-signal
> blocker extraction, "blockers surface early" (the original problem statement's core promise).
> Traced against `design-v2.md` (2026-07-18). Gaps G14–G16. Cast & canon: see S1.

## Setup (beyond canon)

- **T-7** "Final gala artwork" — Design, PIC **Hoa**, end 2026-11-18.
- **T-9** "Print menu cards" — IT, PIC **Minh**, start 11-19, end 11-24.
- Edge **T-7 → blocks → T-9**, created 11-10 by decision D9 (Joe), `created_by_decision_id = D9`,
  upstream handshake auto-confirmed (hackathon rule) → `confirmed`.

## Scenario

> 11-17 15:00, **Design group**, **Hoa:** "Brief đổi rồi 😩 banner chắc trễ vài ngày."
> 11-18 17:00 — T-7's end date passes, no completion.
> 11-20 10:00, **Design group**, **Hoa:** "!progress T-7 done — artwork final đây nhé [file]"

## End-to-end trace (per design-v2 as written)

1. **11-17** — Hoa's message ingests. At the Design group's next threshold, extraction flags it as
   a **weak signal (blocker-ish) → "propose `status=blocked`"** for T-7. As written the doc does
   not say *what entity* that proposal is (decision? task_update? by whom?) — see G16. Suppose it
   surfaces; Hoa is T-7's PIC, so under S2-G7/G9 rules it can auto-apply as her own status update.
2. **11-18 17:00+** — derived lamps recompute *on read*: T-7 `overdue`; T-9 `at-risk` (predecessor
   past its end date; slack = 24 − 18 = 6 days and burning). The design says: notify both PICs +
   **LCA(Lan, Joe) = An**. But nothing *reads* the lamps unless someone opens the dashboard or a
   digest runs — see G14. As written, **nobody is notified.**
3. **11-19** — T-9's planned start arrives with its predecessor unfinished → derived `blocked`
   lamp on T-9. Minh, watching the dashboard, can see T-7's minimal projection (title, status,
   end date, owning team) despite role scoping — the cross-team visibility carve-out. Suppose
   Minh also manually sets T-9 `status=blocked` with a note ("chờ artwork") — a legitimate
   `task_update` by its PIC. Now "blocked" exists **twice**: stored status and derived lamp.
4. **11-20** — Hoa's `!progress T-7 done` marker fires per-message (deterministic, instant): T-7
   `done`. T-9's derived lamp clears; the design's "unblocked — you can start" ping goes to Minh.
   **But T-9's *stored* status is still `blocked`** (Minh's manual update; nothing clears it) —
   see G15.

## What holds up ✅

- The dependency edge as a decision-created object (D9, citable, removable by decision) is clean.
- Cross-project validation and the DAG cycle check have no holes in this flow.
- The visibility carve-out gives Minh exactly the need-to-know slice of Design's board.
- LCA escalation *routing* is well-defined and cheap to compute (An is the manager-chain meet of
  Lan and Joe) — once something actually triggers it.
- The marker path (step 4) shows the deterministic lane doing precisely what it should: instant,
  identity-checked, no AI in the loop.

## Gaps

### G14 — Lamps derive on read, but nothing ever reads them (severity: HIGH)
- **Current:** `blocked`/`at-risk`/`overdue`/`stale` are pure SQL views; notifications for them
  are described ("notify both PICs + LCA") but **no component runs the check**. v1's plan had a
  daily staleness cron (APScheduler) — design-v2 never carried it over. The weekly digest is the
  only scheduled read, so a blocker surfaces up to 6 days late.
- **Expected (your prefs + problem statement):** "blockers surface too late" is the #1 complaint
  the product exists to fix; the review asks for warnings *sent*, not warnings *available*.
- **Fix:** reinstate the **daily radar job** in the backend scheduler: sweep lamps → post to the
  affected teams' groups, tagging PICs (+ LCA when a *cross-team* edge is involved). Dedup and
  escalate rather than re-ping: day 1 PICs only; still unresolved day 3 → add LCA; `urgent` tasks
  ping immediately. Radar and digest both run **flush-before-read** (S2-G8).

### G15 — Two truths for "blocked": stored status vs derived lamp (severity: MEDIUM)
- **Current:** `tasks.status=blocked` (human-asserted via update/decision) and the derived
  dependency lamp are independent. After step 4 they contradict: lamp says T-9 is ready, stored
  status says blocked — dashboard and digest would disagree with each other depending on which
  field they read.
- **Expected:** one coherent answer to "is this blocked, and why" — the review's Note column
  ("blocker details") implies blocked-ness always has a stated reason.
- **Fix:** keep both, but couple them: (a) a stored `blocked` must carry a reason (free-text note
  and/or a dependency ref); (b) when the last blocking predecessor completes, the unblocked ping
  *asks the PIC to confirm resumption* — one tap flips status back (a `task_update`, correctly
  attributed) rather than the system silently unblocking a human-asserted state; (c) dashboard
  renders them distinctly: status chip (asserted) + lamp (computed), never merged.

### G16 — The weak-signal → blocked pipeline is entity-less (severity: MEDIUM)
- **Current:** "blocker-ish → propose `status=blocked`" names no entity, no author, no approval
  lane. Also unspecified: do `requested` (unconfirmed) dependency edges feed the lamps? Can a
  dependency be *removed* ambiently? What happens to a `requested` edge nobody confirms?
- **Fix:** (a) a blocker-ish signal becomes a **proposed `task_update {kind: status→blocked}`**
  routed by S2-G9's author lanes (Hoa = PIC → auto-apply, with the message as citation and its
  text as the reason note); (b) `requested` edges do NOT derive lamps or pings — only `confirmed`
  ones do (prevents an unacknowledged claim on another team's delivery from generating alerts);
  (c) unconfirmed edges expire into the digest's "needs attention" list after N days; (d) edge
  removal is a decision, same gate as creation.

## Verdict

Dependency *modeling* survives contact — edges, DAG, carve-out, LCA routing are all sound. What's
missing is the **engine that makes them matter**: nothing scheduled reads the lamps (G14), so the
exact failure mode the NPO complained about — blockers surfacing late — is still possible with
every individual piece "working". G14 is a one-line scheduler job plus a notification policy;
without it the blocker-radar demo beat doesn't exist.
