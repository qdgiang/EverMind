# S9 — The boundary lands mid-crisis: venue supersession split across windows

> Verifies: non-overlapping threshold windows against the corpus's hero supersession (D1→D2),
> including citation completeness scored by the answer key. Cast/canon: `data/` corpus. Gap G28.
> Complexity: ★★★★☆.

## Grounding (answer key: D1, D2; qa_questions[0])

The venue crisis thread, `aiv-events`, 06-24 morning (m0245–m0255): fee doubled (m0245), old
quote void (m0247), AC broken (m0248), khoa suggests the school gym (m0250), linh checks and
chốt's the move (m0255). Answer key D2 expects **citations m0245 + m0248 + m0255**; hero Q&A #1
expects those plus m0038 (D1).

**Exact window math (counted):** events #100 = **m0250 — khoa's gym suggestion**. So:

- **Window E1** ends at m0250: contains the *evidence* (fee doubled, AC broken) and an open
  suggestion — **no decision**.
- **Window E2** (starts m0251) contains "để mình call their admin office", the gym-is-free
  update (m0253), and the **chốt (m0255, events #105)**.

## Trace (v2 as written)

1. **E1 fires:** a precision-tuned extractor correctly outputs *no decision* (nothing was
   decided). Optionally a weak signal: "venue at risk — fee doubled, AC broken" (→ S8-G27
   ledger, if built). The venue task (created back when D1 was extracted) stays as-is.
2. **E2 fires:** m0255 is a textbook decision — linh even restates the rationale "for the
   record". Extraction produces D2, linked to the venue task (candidates carried it — the
   continuity-via-candidates design **works**: the thread straddled the boundary and still linked
   to the same task). Same-facet detection → "supersedes D1?" → linh (maker of both, rank equal
   to herself) — self-supersession passes the S3-G10 rank gate trivially. D1 → `superseded`.
   The fold's venue facet = Nguyen Du gym. **The lifecycle mechanics are flawless here.**
3. **Citations:** the extractor can only cite messages *in its transcript* — window E2. It emits
   {m0255, m0253, m0251…}. **m0245 (fee doubled) and m0248 (broken AC) are unciteable** — they
   live in E1, which was processed, found decision-less, and will never be revisited.
4. **Scored against the answer key:** D2 extracted ✓, supersession ✓, but citation set fails
   (2 of 3 expected receipts missing). Hero Q&A #1's answer says "because the fee doubled and the
   AC broke" — grounded, per the design, strictly on decisions + citations — so either the Q&A
   answer *lacks the why* (rationale text saves it here only because linh restated it; most
   people don't) or it cites nothing for its central claims.

## What holds up ✅

- Linkage-candidates-as-continuity did its job: no duplicate venue task despite the split thread.
- Precision across the boundary: E1 yielding nothing is correct behavior, not a miss.
- Self-supersession, rank gate, append+flip transaction — all clean on real data.
- linh's "for the record" restatement is a *corpus-author* gift; the design cannot rely on real
  humans doing that.

## Gaps

### G28 — Evidence cited in one window, decision made in the next: citation loss (severity: HIGH)
- **Current:** windows are non-overlapping for extraction *and* for citation visibility. Your
  crawl semantics (each message AI-judged exactly once) forbid re-extraction — but nothing about
  them requires the extractor to be *blind* to prior context when writing receipts.
- **Expected (your prefs):** "receipts, not paraphrase" — every material claim in a decision's
  rationale should be citeable; the answer key encodes exactly that expectation.
- **Fix — read-only context tail, not overlap:** the extraction call for window k includes the
  last M messages (~20) of window k−1 **as context only**: the prompt marks them "already
  processed — do NOT extract new records from these; you MAY cite them." Extraction stays
  exactly-once per message (your rule intact); citations may reach back one tail. Pair with the
  S8-G27 signal ledger (the E1 weak signal "fee doubled/AC broken" carries m0245/m0248 ids;
  promotion attaches them) — either mechanism alone fixes D2's receipts; together they're robust.
- Eval hook: keep D2 in the golden set as the citation-completeness case — it now tests this
  exact mechanism on the exact boundary (the corpus accidentally placed it perfectly).

## Verdict

The supersession machinery — the part you specified most precisely — survives its hardest real
test untouched. What breaks is subtler: **receipts degrade at window boundaries**. The fix
(context-only tail + ledger) preserves your exactly-once crawl while restoring the answer key's
citation contract.
