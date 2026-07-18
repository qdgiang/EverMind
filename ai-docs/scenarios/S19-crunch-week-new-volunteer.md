# S19 — Crunch week, and the volunteer nobody registered (run 2b, vs rev 3)

> Hunt targets: notification volume under fair-week churn, digest under corrections, and a brand
> new volunteer appearing mid-stream — the rotation-IN case. Complexity ★★★★★.

## Scenario

Fair week (07-27 → 08-01): ~40 material events/day across 3 groups; one veto (linh kills a
last-minute "print 500 flyers" decision); and on 07-28 **"Trang"** — a friend khoa recruited
yesterday — joins `aiv-events` and starts posting: "em nhận kê bàn ghế nhé", then two days later
"xong phần bàn ghế rồi ạ" and "!blocked — thiếu 20 ghế, chú bảo vệ nói kho khóa tới thứ 6".

## Trace against rev 3

1. **Volume:** one announcement per decision (not per task); non-urgent batched ~30 min/group;
   radar max 1 ping/task/day, urgent immediate; the veto posts a threaded retraction and the
   Friday digest leads with the correction, flush-before-read keeps it truthful. The week is
   loud but bounded and deduplicated. ✅
2. **Trang's first message:** her `telegram_user_id` is **not in `users`** — the org is a seed
   file (settled #7). Now trace every lane against an unknown author:
   - Ingest ✓ (messages don't require a known author).
   - Her "em nhận kê bàn ghế" is a self-assignment proposal → `proposed`, tagged… to whom? She
     has no team, no manager; `can_decide` and the fallback rules **key off `user_teams` and
     rank, which she lacks.**
   - Her completion "xong rồi ạ" → update lanes ask "is the author a PIC?" — she can't BE one:
     `task_assignments` references `users`.
   - Her `!blocked` marker — identity-checked lane — **fails attribution entirely.**
   - Notifications can't tag her; load can't count her; the persona switcher doesn't know her.
3. Net: rev 3 handles people *leaving* (G33) but not people **arriving** — in an NPO whose
   defining trait is a rotating volunteer base. The system silently drops the contributions of
   exactly the newest, most-in-need-of-onboarding member. This is a real-world expectation
   failure, not an edge case: every demo group will have someone the seed file missed.

## What holds up ✅

Everything volume-related (batching, dedup, cadence caps, retraction, digest honesty) — the
notification design survived its stress week. The failure is confined to identity provisioning.

## Gap

### G44 — No arrival lane: unknown authors fall through every rule (severity: HIGH)
- **Fix — provisional users:** first message from an unknown `telegram_user_id` in a mapped
  group auto-creates `users {status: provisional, rank: 1}` + `user_teams {group's team,
  role_in_team: provisional}` (name from Telegram profile). Provisional members get the full
  member experience — can be PIC, post progress, file proposals, be tagged, be counted in load —
  but the bot posts one line to the group's lead: "👋 Trang joined — confirm membership?"
  Lead's 👍 → `active` (a logged org event); no response → they stay provisional (working, but
  flagged in the digest's team section) — never silently dropped. Departures: provisional users
  who go quiet N days are pruned without the offboarding sweep. Seed file remains the source for
  the *named* cast; provisioning covers the rotation-in reality. (This also generalizes: org
  config changes — new users, membership, new-season teams — are logged config operations, not
  decisions; documented as such.)

## Verdict

**Run 2b: one gap (G44).**

---

**Iteration run 2 result: S18 clean, S19 found G44 → rev 4 required. Not converged
(consecutive-clean counter resets).**
