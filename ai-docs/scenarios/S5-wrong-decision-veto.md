# S5 — The sarcastic budget: a wrong decision goes effective, then gets vetoed

> Verifies: LLM error handling when the *author is authorized*, the correction loop, supersession
> reversal, notification honesty. Traced against `design-v2.md` (2026-07-18). Gaps G17–G21.
> Cast & canon: see S1. Standing state: **D3 "budget 300 USD" (by Joe) is `effective`** on T-1.

## Scenario

> 11-14 11:20, IT group, **Minh:** "Sếp ơi, 300 USD mua đĩa hoa quả hơi căng đấy…"
> 11-14 11:22, IT group, **Joe:** "Ừ thì nâng budget lên 1000 USD luôn cho máu 😂"
> (window threshold crosses that afternoon)
> 11-15 09:00 — Minh notices the bot's announcement and reacts: **/forget D-10** (or 👎).

## End-to-end trace (per design-v2 as written)

1. **Extraction** — the LLM reads the exchange and returns **D10** {description ≈ "nâng budget
   1000 USD", decided_by = Joe, linkage → T-1, citation → Joe's message, confidence 0.55 — it
   *suspects* sarcasm but Joe's phrasing is grammatically a decision}. Same task + facet as D3 →
   "supersedes D-3?" suggestion raised.
2. **Authority** — Joe is authorized → **D10 is born `effective` immediately.** The `confidence`
   field is stored and **consulted by nothing** — see G19. Say a helpful teammate (or Joe,
   absent-mindedly) confirms the supersession suggestion: transaction flips **D3 → `superseded`**,
   back-pointer to D10.
3. **Refold + announce** — T-1's budget facet now folds to 1000 USD. The bot posts the new
   effective decision to the group (material change), tagging Joe and the PICs. The evening's
   radar/digest (if any) would carry it.
4. **Veto** — Minh's `/forget D-10`: per the correction loop, **D10 → `rejected`**, excluded from
   folds and digests. Refold runs. **But D3 is still `superseded`** — nothing un-flips it. T-1
   now has **no effective budget decision at all**: the projection's budget facet is empty, and
   D3's back-pointer dangles at a rejected decision — see G17.
5. **Aftermath** — nothing notifies the group that D10 was retracted (the announcement stands
   uncorrected — see G20); and Minh, a *member*, just unilaterally killed his manager's effective
   decision — see G18.

## What holds up ✅

- Append-only pays off exactly here: nothing was destroyed. D3's body is intact, D10's body is
  intact, every state the task passed through is reconstructable — the veto is *safe* even when
  its bookkeeping is wrong.
- Citations make the audit instant: one click from D10 to Joe's "😂" message and any human sees
  it was a joke. Receipts remain the trust anchor.
- The reasoning popup's time-travel remains truthful throughout (it replays by status + ts).

## Gaps

### G17 — Rejection doesn't resurrect what the rejected decision buried (severity: BLOCKER)
- **Current:** rejecting D10 leaves D3 `superseded` → the budget facet silently vanishes from the
  fold. Silent data loss via a *correction* — the one flow whose whole purpose is restoring truth.
- **Expected (your prefs):** your lifecycle is symmetric in spirit — a new effective decision
  flips its predecessor to superseded, so removing the successor must flip it back.
- **Fix:** rejecting (or un-approving) a decision runs the inverse transaction: for each decision
  it superseded, clear `superseded_by_decision_id` and restore `status=effective` **iff no other
  effective decision supersedes it**; then refold. Same rule handles chains (reject D10 after D11
  superseded it: D3 stays buried — D11 is the current truth).

### G18 — Anyone can veto anything: correction authority is undefined (severity: MEDIUM-HIGH)
- **Current:** the correction loop is inherited from v1 (any 👎/`/forget`) — designed before the
  hierarchy existed. Minh (member) just erased Joe's effective decision, violating review §III
  exactly as S3-G10 does, from the opposite direction.
- **Expected:** subordinates flag; authority decides.
- **Fix:** author lanes again: the decision's **maker** or anyone **ranking ≥ the maker** may
  reject directly; anyone else's 👎/`/forget` files a **challenge** — bot tags the maker
  ("Minh nghi ngờ D-10 — confirm or reject?"), one tap resolves it. Challenges are themselves
  visible in the popup (they're part of the memory).

### G19 — `confidence` is stored but consulted by nothing (severity: HIGH)
- **Current:** an authorized author + a grammatically-decision-shaped joke = instantly effective
  state change with zero human in the loop. The schema's `confidence` field has no consumer.
- **Expected:** precision >> recall — "trust dies with the first hallucinated decision" (v1
  principle, still yours).
- **Fix:** LLM-created decisions go effective without a human touch **only when
  `confidence ≥ threshold`** (config, start 0.8). Below it — even for an authorized author — born
  `proposed`, and the bot asks the author themselves: "Bạn có chốt 'budget 1000 USD' không?" One
  👍 from Joe promotes it (author self-confirmation = the cheapest possible approval). Markers
  and dashboard writes bypass this entirely (they're human-asserted, confidence 1.0).

### G20 — No retraction messaging: the group's last word is the wrong one (severity: MEDIUM)
- **Current:** the bot announced D10; after rejection, silence. Chat's institutional memory now
  contains an uncorrected authoritative-looking announcement — the exact failure mode the product
  exists to prevent.
- **Fix:** rejection of an *announced* decision always posts a correction reply **threaded to the
  original announcement**, tagging the same audience: "❌ D-10 retracted (vetoed by Joe) — budget
  remains 300 USD (D-3)". If a digest already carried it, the next digest leads with corrections.

### G21 — Rejected decisions' visibility in the popup is unspecified (severity: LOW)
- **Current:** the reasoning popup defines a show-superseded toggle (review req) but says nothing
  about `rejected` rows — yet the D10 story (proposed → effective → rejected, challenged by Minh)
  is precisely the kind of institutional memory the popup exists to preserve.
- **Fix:** the toggle becomes "show inactive" and reveals both superseded and rejected (each
  clearly badged, with who rejected and why). Default view stays clean: effective only.

## Verdict

The append-only foundation makes this scenario *recoverable* — nothing is ever lost — but the
correction loop as designed un-does the wrong half: it removes the bad decision while leaving its
burial of the good one in place (G17), and it lets anyone trigger that removal (G18). G17 is a
straight correctness bug in the supersession algebra and must be fixed in the same transaction
design as the supersession write itself; G19 is the cheap insurance that keeps this scenario from
happening at all.
