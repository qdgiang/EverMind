# S10 — The all-hands that never happened (according to the system)

> Verifies: transcript ingestion under threshold windows, speaker identity, late-arriving history,
> meeting-made policies and dependencies. Cast/canon: `data/` corpus + `meeting-2026-06-28.txt`
> (88 turns, `[MM:SS] Name: text`, attendee header). Gaps G29–G31. Complexity: ★★★★☆.

## Grounding (answer key: TD1, TD2, TB1)

The 06-28 all-hands locks three of the corpus's biggest facts: **TD1** fair date = 2026-08-02,
**TD2** budget cap 25M VND (overrun needs linh's sign-off, prizes cut first), **TB1** district
permit pending — the biggest open risk, explicitly gating the public date announcement ("held to
teasers until it clears"). Speakers are display names ("Linh:", "Mai:"); Thao/Huong/Minh absent.

## Trace (v2 as written)

1. **Upload** — `ingestion/transcript.py` parses 88 turns into messages, `source=transcript`,
   channel `meeting/2026-06-28`. Say the upload happens 06-30, two days after the meeting.
2. **Threshold check** — the channel now holds 88 messages. **88 < 100. No window ever fires.**
   No manual flush is scheduled (the design's flush triggers are replay-end and pre-digest — the
   pre-digest flush from S2-G8, *if* built). As designed today: **TD1, TD2, TB1 are never
   extracted.** The fair's date and budget cap — the two most load-bearing facts in the entire
   corpus — do not exist in the system.
3. Suppose flush existed and fired 06-30. Next problems, in order:
   - **Identity:** "Linh:" is a display name; messages carry no `telegram_user_id`. `decided_by`
     resolution (authority gate!) has nothing to key on (G30).
   - **Timestamps:** turns carry meeting-relative offsets (`[02:31]`). Their decisions must enter
     the fold at **06-28 meeting time**, not 06-30 ingestion time — chat from 06-29 (already
     extracted in some window) may reference or refine them. Late-arriving history must slot *by
     event time* (G31): a transcript decision older than an already-effective same-facet decision
     must be born already-`superseded` (with link), never suggested as superseding the newer one.
   - **Scope:** TD2 (budget cap) is a project policy → needs S7-G26; TB1 is an external-wait
     blocker (ward office) → needs S6-G22 fields; and TB1's "announcement held until permit
     clears" is a real **cross-team dependency** (comms announce-task blocked by events
     permit-task) arriving as a *dependency-ish signal from a meeting* → lands as a `requested`
     edge per S4-G16 — verified: the lanes exist, this exercise just proves a transcript can be
     their source.

## What holds up ✅

- The transcript parser contract (one message per turn) fits the canonical Message unchanged.
- The attendee header gives the identity fix a foothold (a name→handle map per meeting).
- Meeting decisions carry rich spoken rationale — once extracted, TD1's rejected alternative
  (Aug 16: not drier, collides with the showcase) is exactly the "why" the reasoning views want.
- TB1's gating sentence shows meetings *produce* dependencies — the edge model receives them.

## Gaps

### G29 — Bulk sources below threshold never extract (severity: BLOCKER)
- **Current:** per-group counters + 100-message threshold. A transcript is a **complete, closed
  unit** — there is no "rest of the conversation" coming to push it over the line. 88 < 100 ⇒
  silence, forever.
- **Fix:** bulk sources (transcript upload; any historical import) flush **on upload completion**:
  the upload IS the window (split at 100 if longer). Live groups keep your threshold semantics
  untouched — this rule is per-source-type, not a change to the crawl.

### G30 — Transcript speakers can't pass the authority gate (severity: MEDIUM)
- **Current:** actor resolution = `telegram_user_id` of cited messages; transcripts have none →
  every meeting decision would fail attribution or land unattributable.
- **Fix:** per-upload speaker map (display name → user handle), seeded automatically from
  `users.name` prefix match + the attendee header, confirmable at upload time. Unmapped speaker →
  decision born `proposed` (safe default), tagged for the uploader to resolve.

### G31 — Late-arriving history: fold by event time, add `recorded_at` (severity: HIGH)
- **Current:** nothing distinguishes *when it was decided* from *when the system learned it*.
  Backdated inserts silently rewrite what dashboards previously showed; supersession suggestions
  compare against "current" state assuming arrival order ≈ event order — a transcript breaks that.
- **Fix:** decisions/updates get `recorded_at` (ingestion time) alongside `ts` (event time). Fold
  and supersession direction order by `ts`; an older-than-current same-facet decision is born
  `superseded` with the link, entering history without disturbing the present. Reasoning popup
  shows both stamps when they differ ("decided 06-28 · recorded 06-30"). Full bi-temporal
  querying ("what did we believe on the 29th?") = roadmap, documented, not built.

## Verdict

The meeting adapter was v1's "great demo-reliability" feature; under v2's threshold crawl it
became a dead letter — the fair's date and budget literally never enter the system. G29 is a
one-rule fix; G30/G31 are the price of taking non-live sources seriously, and G31's
`recorded_at` is cheap insurance the audit scenario (S15) will want anyway.
