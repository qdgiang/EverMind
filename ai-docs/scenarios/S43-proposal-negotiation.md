# S43 — "Sao đắt thế?" — the proposal that becomes a negotiation (run 8e, adversarial, vs rev 8)

> Adversarial target: **the pending state under real human back-and-forth.** Proposals assume
> approve/reject; humans haggle. Complexity ★★★.

## Scenario

duc proposes stage rental 4tr (pending → linh). linh replies "sao đắt thế, hỏi lại chỗ khác
đi" — neither approval nor rejection. Two days of quotes follow; the 48h nudge pings linh
mid-negotiation ("còn đang hỏi mà 🙄"). duc comes back with 3tr2 and files it; the old 4tr
proposal still sits in the queue.

## Trace against rev 8

1. linh's reply: not an affirmation, not a negation → correctly **no approval act** (the
   deterministic list refuses to guess; LLM classification of "sao đắt thế" as rejection would
   be wrong — she's deferring, not refusing). The proposal stays pending. ✅
2. The 48h nudge fires during active negotiation — technically correct, socially noisy. One
   ping per cadence, so bounded. ⚠
3. duc's 3tr2 is a **same-unit, different-value** proposal → per G49 it stays a *separate*
   pending entry (real alternatives are not merged) — two entries in linh's queue. ⚠
4. linh approves 3tr2 → effective-write **sweep** (G11) rejects the 4tr sibling as overruled,
   with the link (G12). The queue self-cleans at resolution; nothing dangles. ✅
5. Bulk lane exists throughout: "dismiss stale" was always one tap if the queue annoyed her. ✅

## Verdict — ACCEPT (settled #15)

### G64 — No "in-negotiation" proposal state (severity: LOW, likelihood: common but harmless)
- **What a fix would cost:** a `needs-info/on-hold` proposal status + who may set it + nudge
  suppression rules + UI — a fourth lifecycle branch to test, for a state whose entire effect
  is *pausing one reminder*.
- **Why accepted:** nothing breaks — the negotiation lives in chat where it belongs; the
  resolution self-cleans via the existing sweep; interim cost is at most one nudge per 48h,
  and the approver can silence it any time with dismiss-stale (re-proposing later is one
  message). The system stays truthful throughout ("pending" IS the truth of a negotiation).
- **Workaround on record:** reply-driven haggling + sweep-on-approve + dismiss-stale. Revisit
  only if real approvers report nudge fatigue.

---

**Run 8 (adversarial) result: 5 scenarios → G60/G62/G63 FIXED in rev 9 (all one-clause);
G61/G64 ACCEPTED under settled #15 with rationale + workarounds. First run triaged under the
acceptance policy: after triage, rev 9 carries zero open unaccepted gaps.**
