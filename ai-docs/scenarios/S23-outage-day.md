# S23 — The day DeepSeek went down (run 4b, vs rev 4)

> Hunt targets: pipeline resilience — LLM outage mid-window, double-fire idempotency, digest
> honesty under backlog, recovery ordering. Verifies rev 4's proactive hardening under a
> realistic worst day. Complexity ★★★★.

## Scenario

07-24, 09:00–21:00: DeepSeek returns 503s all day (its known under-load pattern). During the
outage: `aiv-events` crosses a window threshold at 10:12; mai posts `!decision T-showcase dời
16/8` at 11:00; Trang (provisional) posts `!blocked — thiếu ghế` (bare, no ref) at 14:00; the
daily radar runs at 18:00; recovery at 21:30; two more thresholds cross overnight.

## Trace against rev 4

1. **10:12 window fires → 503 → retry-with-backoff → fail.** High-water mark does NOT advance;
   the window re-queues for the next trigger/flush. No partial output persisted (transactional
   window). Other groups' marks are independent — education/comms unaffected until their own
   calls fail. ✅
2. **11:00 marker (with task ref):** no LLM anywhere in the lane — record created, linked,
   authority-checked (mai, delegation N/A, rank ok on the unit) → **effective during the
   outage.** The deterministic sibling carries the day, exactly the demo-reliability principle. ✅
3. **14:00 bare marker:** record created instantly (deterministic); its *attachment* needs the
   linker (LLM) → attachment fails → the record exists, sits in triage, attaches on recovery.
   Never lost, never guessed. ✅ (Trang being provisional changes nothing — G44 lane is
   identity, not extraction.)
4. **18:00 radar: flush-before-read attempts the pending windows → still 503.** Radar proceeds
   on available data **with the backlog notice** ("extraction backlog: 3 windows pending —
   items may lag"). It pings on marker-derived state (fresh) and pre-outage state (labeled) —
   it does not silently assert currency. Same rule would govern a digest tonight. ✅
5. **21:30 recovery:** pending windows process **in per-group order** (sequential marks);
   outputs enter the fold by event `ts` (G31), so an 09:40 decision extracted at 21:35 slots
   before mai's 11:00 marker decision if same-unit — supersession direction stays truthful;
   `recorded_at` shows the lag in the popup. ✅
6. **Double-fire probe:** the 10:12 window half-persisted before a crash-mid-transaction?
   Transactional = all-or-nothing; re-run upserts by `(window_id, dedup-key)` — no duplicate
   decisions from replaying the same window. ✅
7. **Probe — proposal nudges during outage:** the 48h approver-nudge clock is scheduler-side
   (no LLM) → unaffected. Notification batching unaffected. Overload math unaffected. The
   outage degrades exactly one thing: passive extraction latency — which the backlog notice
   discloses. ✅

## Hunted, found held

Mark-advance-on-success · transactional windows · per-group isolation · marker lane under outage
· bare-marker attachment deferral · flush-failure disclosure (backlog notice) · event-time
recovery ordering · idempotent re-runs · scheduler independence from the LLM.

## Verdict

**Run 4b: no gaps.** The failure mode degrades latency, never truth — and says so.

---

**Iteration run 4 result: S22 clean + S23 clean → second consecutive clean run.
CONVERGED: design-v2 rev 4 holds against real-world expectations across S16–S23
(2 gap-finding runs, 2 clean runs).**
