# S33 — The task that was done four times (run 6e, vs rev 5)

> Hunt target: **contested state between equals.** Multi-PIC was a review requirement; two PICs
> disagreeing about "done" is its natural failure mode. Every individual write is legitimate —
> test what the *sequence* does. Complexity ★★★.

## Scenario

The shared t-shirt task (PICs: minh for production, an for the sales post). Over four days:
minh marks `done` (shirts delivered) → an flips `doing` ("chưa xong, còn bài đăng bán") → minh
flips `done` again ("đấy là task khác chứ??") → an flips back `doing`. Four legitimate PIC
updates, two sincere worldviews, one status field.

## Trace against rev 5

1. **Every write is valid:** both are PICs; the update lane auto-applies each flip; the fold
   shows whoever wrote last. Append-only history records the whole rally faithfully. ✅
2. **But nothing *notices*:** the radar's lamps read the latest value each day — `done` on
   Tuesday, `doing` on Wednesday — never seeing the oscillation itself. The digest reports the
   task completed one week and reopened the next with no eyebrow raised. Dependent-task PICs
   get an "unblocked — you can start" ping on each `done`… then silently lose that state on
   each flip back (rev 5 pings on unblock but nothing retracts the green light). The humans
   involved know there's a disagreement; the system, whose whole job is surfacing coordination
   friction early, is the only party that hasn't noticed.
3. **Root cause is upstream** (one status for two concerns — the S17 "split = compose" answer
   exists), but the *detection* is the system's job: the review's own reasoning-button spec
   exists precisely because "task được update thủ công" needs eyes on it.

## What holds up ✅

Integrity: no write lost, full attribution, popup shows the rally with timestamps — a lead who
*looks* sees everything. Downstream unblock pings fire per the rules. The gap is that nobody is
told to look.

## Gap

### G55 — No contested-state detection (severity: LOW-MED — rare, but exactly the "friction
### surfaced late" the product exists to kill)
- **Fix:**
  - **Contested lamp:** ≥K status flips (default 3) by ≥2 distinct actors within T days
    (default 7) on one task → `contested` lamp; radar nudges the task's lead once: "T-shirts
    flipped done↔doing 4× by minh & an — split it? (production / sales-post)". Suggested action
    is the existing compose-split; one tap creates the child tasks as proposals.
  - **Green-light retraction:** when a task leaves `done` (any lane), dependents who received
    an "unblocked" ping get the inverse ("on hold again — T-shirts reopened"), threaded to the
    original ping. Symmetry rule: any state the bot announced, it un-announces (generalizes
    G20's retraction from decisions to derived pings).

## Verdict

**Gap found (G55)** — small, but it closes a principle-level asymmetry: the system retracted
its *decisions* (G20) and disclosed its *backlogs* (rev 4), yet still let its *green lights*
silently rot. With this, everything the bot asserts is maintained or withdrawn.

---

**Run 6 result: 5 scenarios, 6 gaps (G50–G55; S32 found two). Not clean — rev 6 required.
Previously-verified areas again did not re-break; finds cluster in threads-vs-windows, the
rev-5 bucket's seams, deferred-act staleness, platform ops, and multi-PIC contention.**
