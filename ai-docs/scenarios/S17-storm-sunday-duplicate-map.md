# S17 — Storm Sunday, and the two stall maps (iteration run 1b, vs design-v2 rev 2)

> New territory: **exceptions to standing policies** and **repairing wrong task identity** —
> the two most common "the system said X, reality says Y" moments. Complexity ★★★★.

## Scenario (realistic continuation of the corpus)

- **Part A:** 07-18, typhoon warning. mai in `aiv-education`: "bão vào CN này — nghỉ buổi 20/7
  nhé, học bù CN 27/7 gộp 2 nội dung." (Cancel *this* Sunday's class; make-up next week.)
  Standing policy: D4 — classes Sunday 14:00 (team policy `attr:class-schedule`, effective).
- **Part B:** the stall map exists twice — "stall map" (events, from S-w25 chat) and "sơ đồ gian
  hàng v2" (comms, created via a poster-thread NEW_TASK before project-wide candidates landed).
  Both have history: events one carries duc's updates; comms one carries minh's v2 note. khoa
  notices: "ơ, 2 task trùng nhau kìa."

## Trace against rev 2

**Part A — the exception:**
1. Extraction reads mai's message. Facet-wise it *smells* like `attr:class-schedule` — same
   topic as D4. Rev 2's supersession suspicion raises "supersedes D4?" — mai (maker of D4, rank
   ok) might tap yes reflexively. **If accepted: the Sunday-14:00 policy is superseded by a
   one-week storm cancellation.** The standing schedule — the answer to hero Q&A #2 — is
   destroyed by an exception to it.
2. If instead the suggestion is declined: the cancellation becomes… what? A decision with facet
   `attr:class-schedule` can't be effective alongside D4 (one-effective-per-unit). A note loses
   the authority weight (parents are being told!). **Rev 2 has no way to say "D4 stands; this
   Sunday only is different."**
3. The make-up session ("học bù 27/7") is a clean one-off `NEW_TASK` (kind=project… on an
   ongoing program — kind=`ongoing`'s *instances* are one-offs; works, mildly awkward, not a gap).

**Part B — the merge:**
4. Project-wide candidates (G23) prevent *new* duplicates, but these two already exist — and
   linkage is probabilistic, so duplicates WILL keep occurring at some rate. Rev 2 has no merge:
   khoa can cancel one task, but then its history (duc's updates, citations, a dependency from
   the printing task) is stranded on a canceled husk; the popup on the survivor tells half the
   story; Q&A may cite the canceled one.

## What holds up ✅

Part A's *detection* is right (same-topic suspicion is correct behavior); suggestion-not-autoflip
is the only thing standing between D4 and accidental destruction — but it's a human dodging a
trap the model set. Part B: cancel exists, decisions are append-only so nothing is *lost*, and
G23 has stopped the bleeding at the source.

## Gaps

### G42 — No exception semantics: one-off deviations fight the standing policy (severity: HIGH)
- **Expected:** "nghỉ CN này" must coexist with "CN hàng tuần 14:00" — reality has both truths.
- **Fix:** decisions gain optional **`effect_window {from, until}`**. A windowed decision on an
  occupied unit does NOT supersede and is NOT blocked by one-effective-per-unit: it *shadows*
  the standing decision within its window and auto-expires after. Fold: windowed effective
  decisions override standing ones only inside their window. Extractor rule: exception language
  ("CN này", "tuần này thôi", "riêng buổi 20/7") → windowed decision, never a supersession
  suggestion. Popup renders "⏸ exception 20/7 (expired)" under the standing policy.

### G43 — No task merge: duplicate identities can't be repaired (severity: MEDIUM-HIGH)
- **Fix:** a `merge` op (task-scoped decision on the survivor): absorbed task →
  `status: merged`, `merged_into: survivor`. Effects, in-transaction: decision_tasks /
  task_updates / signals / citations re-point (or union at read time via the redirect);
  dependencies re-point with dedup; assignments union; the absorbed task's same-unit effective
  decisions enter the survivor's supersession resolution (newest per unit wins, others flip
  superseded — the normal machinery, reused). Popup on the survivor shows the merged lineage;
  the husk redirects. Authority: lead over any owning team of either task. Split = compose
  (create children + refine parent) — already expressible; documented, not a new op.

## Verdict

Run 1b: **two gaps (G42, G43)**. Both are "reality is layered" problems — a policy plus its
exception, one workstream behind two records — and both fixes reuse the existing machinery
(windowed fold; supersession resolution on merge) rather than adding new concepts.

---

**Iteration run 1 result: 3 gaps (G41, G42, G43) → design-v2 rev 3 required. Not converged.**
