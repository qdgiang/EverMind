# S29 — "Ok chốt": the two-word decision (run 6a, vs rev 5)

> Hunt target: **terse reply-decisions.** Half of real Telegram decision-making is a two-word
> reply to something said days ago. Windows are contiguous and the context tail only reaches
> the previous window's last ~20 messages — replies reach *anywhere*. Complexity ★★★★.

## Scenario

- 07-02, duc posts a detailed sound plan-B proposal (m-old): "nếu vendor im tiếp thì thuê bộ
  loa của trường Kim Liên, 1tr8, mình đã hỏi rồi".
- Nothing happens for three weeks (two full windows pass).
- 07-23, linh **replies** to that message: **"ok chốt nhé"**. That's the entire message.
- Same week, khoa replies "duyệt" to the bot's own "📋 Proposed — awaiting @khoa…" announcement
  of a pending buddy-pairing proposal.

## Trace against rev 5

1. **Extraction sees:** `[reply→m-old] linh: ok chốt nhé`. The window transcript contains the
   reply but **not m-old** — it's three weeks outside the window AND outside the context tail
   (which only spans the previous window's tail). Chốt *what*? The extractor has: an authorized
   author, an affirmation, and a `thread_ref` pointing at text it cannot see. Honest outcomes:
   UNLINKED-triage (the decision of record for the plan-B never forms) or a hallucination risk
   if the model guesses from ambient chatter. **The single most common real-world decision
   shape — authority affirming a subordinate's proposal — is structurally unreadable.**
2. **Citations:** even if a human triages it, the *evidence* is m-old (the plan's content) +
   the reply (the authority act). Rev 5 citations can only point at what extraction saw.
3. **khoa's "duyệt" reply to the bot announcement:** rev 5's approval acts are the dashboard
   tap and the 👍 reaction. A textual reply to the proposal announcement — the most natural
   approval gesture in chat — has no defined effect. (Bots receive replies to their own
   messages regardless of privacy mode, so the signal is reliably available.)

## What holds up ✅

- `thread_ref` was captured at ingest all along — the data needed for the fix already exists.
- Authority/attribution rules need no change: linh's reply is a cited authority act; duc's
  m-old is content evidence. The lifecycle (proposal → effective) fits perfectly once the
  extractor can *see* both halves.

## Gap

### G50 — Reply-target hydration + approval-by-reply (severity: HIGH — this is how real
### groups decide)
- **Fix:**
  - **Hydration:** for every window message whose `thread_ref` targets a message outside the
    window, inject the target (and its direct parent, ≤2 hops) into the prompt as
    `[replied-to, 2026-07-02] duc: …` — marked context-only for extraction (never re-extracted;
    exactly-once preserved) but **citable**. Citations for the resulting decision = the reply
    AND its target — which is precisely the receipt a human would want.
  - **Approval-by-reply:** an affirmation reply ("ok chốt", "duyệt", "approve") by a user with
    sufficient rank, targeting either a pending proposal's source message or the bot's proposal
    announcement, is an **approval act** (same lane as the 👍 reaction; the reply is cited as
    the approval evidence). Negations ("thôi", "khỏi") likewise map to reject. Deterministic
    short-list of affirmation/negation forms first; LLM classification only for ambiguous text.

## Verdict

**Gap found (G50).** The window model was built for self-contained conversation; threads are
the escape hatch real users take daily. Hydration closes it without touching the
exactly-once crawl.
