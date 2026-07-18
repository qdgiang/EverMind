# S32 — The group upgraded and nobody told the bot (run 6d, vs rev 5)

> Hunt target: **platform ops that silently sever capture.** A memory system's worst failure is
> not wrong data — it's a quiet hole where days of chat never entered. Complexity ★★★.

## Scenario

- 07-26, `aiv-events` hits Telegram's group limits and **auto-upgrades to a supergroup** — the
  platform assigns a NEW chat id (the old one dies; Telegram sends a final `migrate_to_chat_id`
  service message).
- 07-28, an admin tidying members **accidentally removes the bot** from `aiv-comms`. Nobody
  notices — the group keeps chatting; the bot hears nothing.
- 08-01 (Friday 23:30 +07): mai posts a decision; the weekly digest window is "this ISO week" —
  computed in which timezone? Server runs UTC; 23:30 Friday +07 is 16:30 UTC — same week either
  way, but Sunday 23:30 +07 vs UTC flips the week bucket.

## Trace against rev 5

1. **Supergroup migration:** `chat_groups` keys on `platform_chat_id`. After migration, updates
   arrive from an unknown chat id → the mapping misses → messages from the org's busiest group
   land unrouted (or dropped). Rev 5 has no rule, though the platform *announces* the migration
   (`migrate_to_chat_id` on the last old-id update). Capture from `aiv-events` silently ends.
2. **The kicked bot:** the API sends a `my_chat_member` update at kick time (status →
   `kicked`/`left`) — one chance to notice, then silence forever. Rev 5's backlog honesty (G-rev4)
   covers *LLM* downtime, not *ingest* death: windows simply never fill, the radar reads a calm
   week, the digest happily reports less and less. **Silence is indistinguishable from peace.**
3. **Week boundaries:** digests, `effect_window` resolution ("CN này"), staleness day-counts —
   all date math. Rev 5 never names the org timezone; a UTC server shifts late-evening events
   across day/week lines (+07 is 5–7h ahead), misfiling Sunday-night decisions into next week's
   digest and sliding "due today" lamps.

## What holds up ✅

Backlog honesty for LLM outages, per-group mark isolation, and the replay/eval paths (no
platform in the loop). And both platform signals needed below already exist in the Bot API —
the design just never subscribed to them.

## Gaps

### G53 — Capture liveness: migration handling + kicked-bot detection (severity: MED-HIGH —
### silent memory holes)
- **Fix:** (a) on `migrate_to_chat_id`, auto-update the `chat_groups.platform_chat_id`
  (logged config op; history untouched — messages key on their own ids). (b) Subscribe to
  `my_chat_member`: on kicked/left/permissions-lost, alert the coordinator immediately
  ("capture from aiv-comms stopped — re-add the bot"). (c) Belt-and-braces daily self-check per
  mapped group (`getChatMember(self)`), since updates can be missed during downtime; digest
  carries a capture-health line when any mapped group is dark ("⚠ no capture from aiv-comms
  since 07-28").

### G54 — No org timezone (severity: LOW — one config line, many small lies without it)
- **Fix:** `ORG_TIMEZONE` (demo: `Asia/Ho_Chi_Minh`). All week bucketing, day-count lamps,
  digest scheduling, and relative-date resolution ("CN này", "thứ 6") compute in org time;
  storage stays UTC/aware timestamps (already the case).

## Verdict

**Two gaps (G53, G54).** Both are the platform-ops tail of the honesty principle: the system
already refuses to present lagging data as current — it must equally refuse to present a
severed feed as a quiet week.
