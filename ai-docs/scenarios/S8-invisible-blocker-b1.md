# S8 — The sound vendor who never replies: a blocker with no single loud message

> Verifies: weak-signal extraction across threshold windows — the corpus's planted *hero* implicit
> blocker. Cast/canon: `data/` corpus. Gap G27. Complexity: ★★★☆☆.

## Grounding (answer key: B1)

B1: "Sound-system rental vendor not replying" — owner duc, waiting since 06-20, **implicit: 3
passing mentions, never stated as a blocker**, still open at corpus end (W28 status: "sound
supplier STILL not locked, plan B being prepared").

Window placement (events channel, 216 msgs → windows E1 = events #1–100, E2 = #101–200, tail #201–216):

| Mention | Msg | Events ordinal | Window |
|---|---|---|---|
| 1st passing mention | m0200 | #74 | **E1** |
| 2nd passing mention | m0297 | #119 | **E2** |
| 3rd passing mention | m0426 | #171 | **E2** |

## Trace (v2 as written)

1. **E1 fires** (~06-20): one passing mention of a quote sent and no reply. Alone, this is *below*
   any honest weak-signal threshold — a precision-tuned extractor must NOT flag a blocker from one
   grumble (that is exactly what distractor X1, the self-resolved signup scare, is planted to
   punish).
2. **E2 fires** (~07-05): two more passing mentions, ~50 messages apart *within* the window. Even
   if the LLM connects them, it has no memory that E1 contained the first mention or that the
   quote was sent 06-18 — the `since` date and the pattern's third leg are in a window it will
   never see again.
3. Result: each window sees a sub-threshold fragment. **B1 is structurally undetectable** by
   window-isolated extraction — not a prompt-quality problem, an architecture one. The answer
   key's hardest planted case fails by design.
4. Knock-on: no blocker → no staleness clock → nothing for the radar (S4-G14) to escalate → the
   W28 "plan B" scramble happens exactly as late as it would without the product. The problem
   statement's core promise — surface blockers *early* — is unmet on the flagship example.

## What holds up ✅

- The precision instinct is correct: refusing to flag from mention #1 is right (X1 proves it).
  The failure is having nowhere to *remember* mention #1.
- Marked blockers (B2, B4) are immune — the marker lane catches them instantly. The gap is
  exactly the unmarked-implicit class, which is the class the AI layer exists for.

## Gaps

### G27 — Weak signals need memory across windows: a signal ledger (severity: BLOCKER for the demo)
- **Current:** each extraction call sees its window + open-task candidates. Weak signals that
  don't clear the bar are discarded — cross-window accumulation is impossible.
- **Expected (your prefs):** the batch flow is yours and stays; but the answer key you built
  plants B1 precisely to test accumulation ("3 passing mentions, never stated as a blocker").
- **Fix:** a small `signals` table: `{id, kind: blocker|dependency|…, task_or_topic, excerpt,
  message_id, ts, window_id}`. Extraction's output schema gains a `weak_signals[]` list (cheap for
  the LLM — it already noticed them); they persist without touching the projection. The *next*
  window's prompt includes open signals for its candidates ("prior signals on this topic: quote
  sent 06-18, no reply as of 06-20; still waiting 07-01"). Promotion rule: ≥2 corroborating
  signals (or 1 signal + staleness) → propose `status=blocked` with `waiting_on`/`since` from the
  ledger (G22 fields) and **citations = all accumulated mentions** — which is exactly the
  three-message citation set the answer key expects for B1. Signals expire if contradicted
  (vendor replies) or after N quiet days.
- Also fixes: distractor discipline is preserved (one signal never promotes alone), and the
  ledger gives the digest a "rumbling risks" line distinct from confirmed blockers.

## Verdict

This is the second architecture-level miss grounded in the corpus (after S7's scope gap): the
threshold-window design you specified is right for decisions, but weak signals need a persistent
ledger threaded through those windows, or the product's marquee "caught the blocker nobody
declared" beat cannot happen.
