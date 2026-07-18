# S16 — August 2nd, and the morning after (iteration run 1a, vs design-v2 rev 2)

> New territory: **the end of a project's life.** The corpus ends 07-12 with "23 days to the
> fair"; this scenario plays the fair weekend and the week after against rev 2. Complexity ★★★★.

## Scenario (realistic continuation of the corpus)

- 08-02: the fair happens. Frantic morning chat; donation box counted twice ("first count 18tr4!",
  huong posts VietQR total 08-03); duc returns the genset 08-04; minh's leftover 30 shirts to be
  sold online "sometime"; thao dumps 400 photos.
- 08-03: `project.end_date` (08-02) has passed. Open at that moment: sound plan-B task (moot —
  the backup PA worked), banner-reprint (never done, nobody cares now), permit task (`done`),
  thank-you posts (comms, genuinely in progress), equipment-return (doing), "sell leftover
  shirts" (new, no end date), retro all-hands scheduled 08-09 with transcript uploaded 08-11.

## Trace against rev 2

1. **Fair-week mechanics hold:** urgent pings bypass batching; flush-before-read keeps the 08-01
   digest truthful; the donation counter (huong's totals) rides as team-note quote or optional
   counter — per §Digest, fine.
2. **08-03, radar runs.** `end_date` passed ⇒ **`overdue` fires on every open task** — including
   the moot plan-B and the abandoned banner-reprint. Day 3: escalations to LCA. The system's
   loudest week is the week the project is *over* — pure noise, exactly the false-ping erosion
   the design warns against. Rev 2 has **no concept of "the project ended."**
3. **New post-fair tasks** ("sell leftover shirts"): `end_date` defaulting says project.end − 1
   day = **08-01, in the past**, `end_date_defaulted=true` + warning. Defaulting is now actively
   wrong for every task created after project end.
4. **Retro decisions** (08-09/08-11): "next year book sound 6 weeks out", "keep free-entry
   format" — project-scoped policies; transcript flush + speaker map + late-arrival ordering all
   work (G29/G30/G31 verified ✓). But they attach to a project that is conceptually finished —
   nothing marks it so; the dashboard shows a live project forever.
5. **The wrap-up story** — "what shipped / what didn't / what we decided for next time" — is
   THE artifact an NPO wants from this week. Rev 2's digest is a *weekly delta*, not a project
   retrospective; no view assembles it.

## What holds up ✅

Urgent lanes, flush-before-read, counters/wrap-quotes, transcript pipeline (G29–G31), policy
scope for retro decisions, cancel-with-reason for the moot plan-B (a decision, works today).

## Gap

### G41 — Projects have no lifecycle: nothing ends, so the end is noise (severity: HIGH)
- **Current:** `projects {id, name, end_date}` — a date with no semantics after it passes.
  Overdue storms, nonsense defaulting for post-end tasks, no closure artifact.
- **Expected (real world):** events END. The week after is triage-and-archive, not alarms.
- **Fix:** `projects.status: active|closing|closed`.
  - `end_date` passing (or coordinator decision) → `closing`: radar switches from overdue-pings
    to ONE **close-out sweep** — a checklist posted to each team: every open task proposed as
    `done` / `canceled(obsolete)` / `migrate to ongoing` (each resolution = a normal decision;
    "sell leftover shirts" migrates, kind=ongoing, defaulting exempt).
  - All resolved (or coordinator decision) → `closed`: a generated **retrospective digest**
    (shipped / didn't-ship / decisions incl. next-time policies / final counters), archived;
    project drops from active views; ingestion of stragglers (late transcripts) still allowed —
    they append to the archive.
  - Defaulting rule amended: in `closing|closed`, new tasks default to no-end + warning instead
    of a past date.

## Verdict

Run 1a: **one gap (G41)** — rev 2 models a project's life perfectly and its death not at all.
Everything else in a deliberately messy week held.
