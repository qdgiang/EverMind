# S28 — Trang discovers markers (probe run 5e, vs rev 4)

> Hunt target: **input hygiene under enthusiasm.** Not malice — a keen new volunteer who just
> learned the `!decision` trick. Every gate holds individually; test what the *aggregate* does
> to the humans downstream. Complexity ★★★.

## Scenario

Trang (provisional, S19) reads the pinned how-to. In one afternoon she posts:
- `!decision chốt mua 50 ghế nhựa` … then, unsure it "worked", **pastes the same marker 4 more
  times**;
- `!decision T-banner đổi màu xanh` (someone else's task, comms);
- `!blocked T-roster thiếu người` (khoa's task — she's not its PIC);
- and asks khoa in-thread: "sao bot chưa làm gì vậy anh?"

## Trace against rev 4

1. **Integrity: fully held.** Every marker from a rank-1 provisional → born `proposed`; zero
   task state mutated; the banner-color proposal tags comms' lead; the blocked assertion is not
   from a PIC → confirm-lane asks khoa. No gate failed. ✅
2. **But the humans:** phuong's approval queue now holds **5 identical chair proposals** (each
   will nudge her at 48h — five times), plus a banner one; khoa got a confirm ping; the group
   saw 7 bot announcement lines ("📋 Proposed — awaiting…") in one afternoon (batching compresses
   timing, not count). The digest lists 6 pending proposals, 5 of them the same chairs.
   Rev 4 has **no dedup of identical proposals, no bulk actions for approvers, no coaching
   feedback to the enthusiastic sender.** The failure mode isn't corruption — it's that the
   approval surface, the product's front door for leads, silts up. Trust erodes by annoyance
   (the same way false radar pings would), and the review's own worry — approval spam was
   G13's theme for *extracted* musings — recurs on the *marker* lane where G13's
   consistency rule doesn't apply.

## What holds up ✅

Authority gates, provisional lane, confirm-lanes, projection integrity, batching timing — the
system is *safe* under enthusiasm; it's just not *pleasant*. And her question to khoa is the
tell: silent `proposed` states confuse newcomers even with G5's announcements (she didn't read
them as feedback *to her*).

## Gap

### G49 — No proposal hygiene: identical-dedup, bulk actions, sender coaching (severity:
### LOW-MED — UX debt on the highest-traffic human surface)
- **Fix:**
  - **Identical-proposal collapse:** a new proposal matching a pending one on (unit, op, value)
    merges into it — citations union, proposers listed, ONE queue entry, one nudge clock.
    (Same-unit *different*-value pendings stay separate — those are real alternatives.)
  - **Approver bulk actions:** `approve all / dismiss all from <person> / dismiss stale` on the
    pending queue (dashboard + a compact bot reply form). Dismissals are `rejected` with reason,
    visible under show-inactive as always.
  - **Sender feedback & coaching:** the bot replies to the *sender* of a marker-proposal once,
    directly ("Got it — sent to @phuong for approval. No need to repost 👍"); a repeat-paste
    within the window triggers the collapse silently plus one gentle tip. Soft per-user
    marker-rate note to the lead only if it persists (no hard caps — enthusiasm is a feature in
    a volunteer org).
  - Digest: pending proposals grouped by unit (chairs ×1, not ×5) and by proposer for leads.

## Verdict

**Gap found (G49)** — the only one this run that's about ergonomics rather than truth. Worth
fixing precisely because approvals are where leads live; a silted queue is how they stop
reading the bot.

---

**Probe run 5 result: 5 scenarios, 5 gaps (G45–G49) — all NEW territory (platform mutability,
media, program/team homes, governance edge, hygiene). The previously-converged semantics
(S18–S23's clean areas) were not re-broken. Design rev 5 required.**
