# S24 — The edited contract price (probe run 5a, vs rev 4)

> Hunt target: **the source evidence mutates.** Telegram users edit messages constantly; bots
> receive `edited_message` updates (but NO delete notifications — the API has none). Rev 4
> treats `messages` as "immutable source evidence, unchanged from v1". Complexity ★★★★.

## Scenario

- linh's m0245 ("rent is now 2tr4") is cited by effective decision D2. On 07-25 she **edits** it:
  "rent is now 2tr4 *(update: they called back, 2tr6 from next year)*".
- minh edits his `!decision` marker message 3 minutes after posting: "120 shirts" → "130 shirts"
  (typo fix — the real order was always 130).
- duc **deletes** a heated message about the sound vendor that a blocker record cites.

## Trace against rev 4

1. **Cited-evidence edit:** the bot receives `edited_message` for m0245. Rev 4 has no rule: the
   Message row is "immutable"… so either we ignore the edit (our cached text now differs from
   what everyone sees in Telegram — the receipt lies) or overwrite it (the decision now cites
   text that wasn't there when it was decided — the receipt lies the other way). **Both wrong;
   nothing specified.**
2. **Marker edit:** does the marker lane re-fire on `edited_message`? Unspecified. Re-fire →
   duplicate decision (120 AND 130). Don't re-fire → the record says 120 forever, the chat says
   130 — and minh *reasonably expects* a 3-minute typo fix to count.
3. **Delete:** no notification exists — undetectable by design of the platform. Our cached text
   silently outlives the source; a citation deep-link would 404 while the popup shows text the
   author withdrew. Consent posture unstated.

## What holds up ✅

Decision bodies are append-only and never derived from re-reading messages, so no *record*
silently mutates — the blast radius is confined to receipts. And the citation model already
stores per-message links, which makes revision-pinning a natural extension, not surgery.

## Gap

### G45 — Message mutability: edits/deletes vs "receipts, not paraphrase" (severity: HIGH —
### this is the trust anchor)
- **Fix:**
  - `messages` gains `current_rev`; new table `message_revisions {message_id, rev, text,
    edited_at}`. Every `edited_message` appends a revision; nothing is overwritten.
  - **Citations pin the revision**: `decision_citations` stores `rev_at_capture`. Views render
    the pinned text; if `current_rev > rev_at_capture`, the record shows an **"evidence edited
    after capture"** badge with a diff link, and the bot nudges the record's maker once:
    "m0245 was edited — still stands? 👍 / reissue."
  - **Markers are idempotent by source message**: a marker record is keyed to its message_id.
    Edits within a grace window (~10 min) **amend** the record in place (typo lane — minh gets
    his 130). Later edits never mutate records: they set the badge + maker nudge, same as any
    cited-evidence edit.
  - **Deletes:** undetectable via Bot API — documented honestly. Cached revisions are retained
    under the consent posture (bot presence = visible capture; the published record schema says
    so); popup labels the text "cached copy" when the deep-link is known-dead (detected lazily
    on click-through failure, not promised proactively).

## Verdict

**Gap found (G45).** Rev 4's receipts assumed a write-once world; Telegram isn't one. The fix
keeps records append-only and makes receipts *versioned* rather than pretending the source
can't move.
