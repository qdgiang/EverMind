# S11 — chi Yen: the person who left, and still blocks two teams

> Verifies: how the model handles people outside/beyond the org — the volunteer-rotation problem
> the product was founded on. Cast/canon: `data/` corpus. Gaps G32–G33. Complexity: ★★★★☆.

## Grounding (answer key: B2, B5; personas note)

"Former treasurer **chi Yen** is mentioned but never writes." Two planted blockers wait on her:
- **B5** (comms, since 06-12): AIV Facebook page admin access left with her; an (social media)
  blocked; huong chasing via Zalo. Resolved 06-15 (m0103).
- **B2** (comms, since 06-22, `!blocked` m0218): e-banking access not handed over → finance
  blocked (sponsor payments, reconciliation). Resolved 07-02 (**m0370 — comms tail, flush-only**).

## Trace (v2 as written)

1. **B2's marker fires** (m0218, huong): instant blocked record — but on *what task*? (bare
   marker → S6-G24), and `waiting_on = chi Yen`… **who?** She is not in `users` (correctly — she
   is gone and never writes). The waiting-on party is a free-text string at best (S6-G22).
2. **B5, unmarked**, needs weak-signal work (m0070/m0072 → promoted or missed per S8-G27).
3. **The aggregation that never happens:** two teams, two blockers, **one root cause — the same
   departed person**. With `waiting_on` as free text ("chi Yen", "chị Yến", "the old
   treasurer"…), nothing can group them. The radar pings two teams separately; nobody sees "chi
   Yen holds 2 org-critical accesses" — which is the single most actionable sentence in this
   whole storyline, and precisely the institutional-memory failure the problem statement
   describes (knowledge leaves with people).
4. **Resolution latency:** B2's resolution (m0370, "access recovered") is plain chat in the
   comms flush-only tail — with S2-G7 unfixed it never registers; even fixed, it registers at
   final flush. The blocker shows *open* for the rest of the replay. (Same class as S2-G8.)
5. **The forward-looking version:** khoa announces he's rotating out next month. The system
   holds: his PIC-ships, his open proposals, dependencies through his tasks — everything needed
   to generate an offboarding checklist. **No mechanism exists**: `users` has no lifecycle state,
   and nothing sweeps a departing person's holdings (G33).

## What holds up ✅

- Not making chi Yen a `user` is correct — actors must be people who can act. The gap is the
  *reference*, not the membership.
- The blocked→resolved arc itself (status flip by owner, staleness clock while open) maps cleanly
  onto task_updates once G22/G27 exist.
- Every claim stays cited: the Zalo-chase saga is reconstructable from receipts. And the eventual
  handover (m0370) resolving a 10-day-old marker shows the `since`-based aging story working.

## Gaps

### G32 — External parties are strings, so risks never aggregate (severity: HIGH)
- **Current:** vendors (InTheXanh, sound supplier), institutions (ward office, school IT), and
  departed people (chi Yen) exist only inside note text. Cross-blocker grouping, "who do we chase
  hardest", and the handoff doc's "external contacts" section are all impossible.
- **Fix:** tiny `parties` table `{id, name, aliases[], kind: person|vendor|institution,
  contact_note?}`; `waiting_on` becomes an optional FK + free-text fallback. Extraction proposes
  party matches from aliases (fuzzy, confirm-on-first-use). Radar groups open blockers by party:
  "3 teams waiting on chi Yen/InTheXanh/ward office" — a digest line that writes itself.

### G33 — No user lifecycle, no offboarding sweep (severity: HIGH — it's the founding pitch)
- **Current:** `users` rows are eternal. A departed member still appears in persona switchers,
  load views, and notification fan-outs (ghost pings); nothing forces reassignment of their
  tasks.
- **Fix:** `users.status: active|departing|departed` (+ `departed_at`). Setting `departing`
  triggers the **offboarding sweep** — a generated checklist decision-set: open tasks to
  reassign (each a proposed `assign_set` for their lead), pending proposals to re-route, parties
  only they were chasing, accesses mentioned in their blockers. Setting `departed` excludes them
  from fan-outs and load, keeps history intact (snapshots already make old decisions safe).
  This is F12's onboarding brief mirrored — same queries, opposite direction — and it is the
  literal answer to "chi Yen left and took the bank access with her."

## Verdict

The corpus's ghost character is the product thesis in miniature: v2 currently *records* the chi
Yen saga but cannot *see* it (no party identity) and could not have *prevented* it (no departure
mechanism). Both fixes are small tables + one sweep, and G33 doubles as a demo beat with more
emotional weight than any dashboard view.
