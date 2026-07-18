# S20 — The rumor, the challenge, and the unanswered question (run 3a, vs rev 4)

> Hunt targets: stale beliefs circulating in chat, a member disputing an effective decision,
> unanswered asks, Q&A truthfulness under supersession + exceptions. Complexity ★★★★.

## Scenario

- 07-22, `aiv-comms`: a stall vendor's rep (relayed by an) asks "fair vẫn ở Phuong Liet đúng
  ko?" — the venue changed a month ago (D2 superseded D1).
- an, unsure herself: "/ask fair ở đâu?" — then 👎-reacts D2's record ("tưởng vẫn Phuong Liet??").
- huong asks "ai có contact xưởng in dự phòng ko?" — nobody answers for 4 days.
- A judge-style probe: "/ask lịch học CN tuần này?" — during the storm-exception week (S17's
  windowed decision active).

## Trace against rev 4

1. **Stale rumor:** the vendor question is not a decision, not a contradiction *by an authority*
   — extraction yields at most an `ask` signal. The projection is untouched (rumors can't write).
   `/ask` answers from **effective** decisions: Nguyen Du gym, citing D2, noting it superseded
   D1 (supersession-aware answer — the hero Q&A behavior). ✅
2. **The challenge:** an (member, rank 1) 👎 on D2 (maker linh, rank 3) → rank < maker ⇒ **files
   a challenge**, never a rejection. Bot tags linh: "an nghi ngờ D2 — confirm or reject?"
   linh 👍-confirms; the challenge is recorded and visible under show-inactive (part of the
   memory: someone doubted, it was reaffirmed, receipts attached). Projection never wobbled. ✅
3. **The unanswered ask:** `ask` signal opens 07-22; no answering message correlates; after N
   days the digest's "asks past N days" line surfaces it with the citation — huong's question
   stops being lost in scrollback. (Answered asks: a reply in-thread correlates → signal
   expires quietly.) ✅
4. **Q&A under an exception window:** the class-schedule unit has D4 standing + the windowed
   storm decision shadowing 07-20 only. Fold-at-date logic answers "tuần này" with the
   exception (nghỉ 20/7, học bù 27/7) while "lịch học nói chung" answers D4 — the effect_window
   semantics defined in rev 3 give the Q&A layer exactly the data to do this; grounding rules
   (effective + windowed decisions only, cited) hold. ✅
5. **Probe — challenge pile-up:** three more members 👎 D2 after the vendor rumor spreads. Rank
   lane: all become challenges to linh; notification batching dedups into one nudge listing all
   challengers (per-decision announcement rule). No spam loop. ✅

## Hunted, found held

Rumor-cannot-write · supersession-aware Q&A · challenge-vs-reject routing by rank · challenge
visibility as memory · ask lifecycle (open → digest → expire-on-answer) · windowed-exception Q&A
· challenge dedup under batching.

## Verdict

**Run 3a: no gaps.** The read path (Q&A/digest) and the dissent path (challenges) both behave
per rev 4 with no rule-stretching.
