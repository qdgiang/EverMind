# S25 — The contract is a photo (probe run 5b, vs rev 4)

> Hunt target: **non-text messages.** The corpus is text-only; real Telegram is not. Photos of
> signed contracts, voice-note blockers, forwarded sponsor PDFs are everyday evidence.
> Complexity ★★★.

## Scenario

- linh posts a **photo** of the signed gym contract, caption "kí xong nhé ✅" — this IS the
  completion evidence for the venue task.
- thao sends a 40-second **voice note**: "bên in bảo hoãn tới thứ 6…" (a blocker, spoken).
- huong **forwards** the sponsor's message from her DM into `aiv-comms`: "TechViet confirms 5tr
  sponsorship" — sender is huong, author is the sponsor's rep (a non-member).

## Trace against rev 4

1. **Photo with caption:** `Message.text` is the v1 contract's only content field. Where does
   the photo go? Unspecified — the adapter either drops the message (evidence lost) or stuffs
   the caption into `text` (works by accident, media unreferenced: the popup can never show the
   contract). The *strongest evidence in the project* — a signed document — is the weakest
   citizen in the store.
2. **Voice note:** no text at all. Ingestion has literally nothing to persist under the v1
   shape; the blocker it carries is invisible to extraction. (Whether to transcribe is a scope
   question; whether the message can *exist* is not.)
3. **Forward:** Telegram supplies `forward_origin`. Rev 4's attribution rule — maker must be
   among cited authors — sees author=huong asserting the sponsor's words. That is exactly the
   **relay lane** (born proposed, claimed source tagged)… except the claimed source is a
   non-member, so it routes like a party statement, and rev 4 never says forwards feed the
   relay lane or that `forward_origin` is kept.

## What holds up ✅

- The relay lane's *shape* absorbs forwards perfectly once forward metadata exists — no new
  lifecycle needed (a forward is a structured, platform-verified relay).
- Parties (G32) give the sponsor's rep a home as the *origin* of forwarded claims.
- Extraction semantics need no change: captions are text; the window transcript just gains
  typed lines ("[photo] kí xong nhé ✅").

## Gap

### G46 — Media and forwards aren't representable in the Message contract (severity: MED-HIGH
### for real use; LOW for the text-only demo corpus)
- **Fix:**
  - `messages` gains `kind: text|photo|video|file|voice|sticker|system`, `media_ref?`
    (platform file_id + mime + filename), `forward_origin?` (author name/id or channel, per
    Bot API). `text` holds the caption (may be empty).
  - Extraction: media messages enter windows as `[kind] caption` lines; a media message with no
    caption is context, not extractable content. Citations render kind-aware (📷/🎤/📎 + caption
    + fetch-on-click via media_ref).
  - Forwards: route through the **relay lane**; `forward_origin` is the claimed source. Origin
    is a member → tag them for self-confirm; origin is external → the decision needs an
    authorized member's confirm (huong's own 👍 if she has authority, else her lead's), and the
    origin can be linked to a `party`.
  - Voice transcription: **roadmap**, stated (store the file now; transcribe later — records
    can cite the voice message itself meanwhile).
  - Demo note: corpus stays text-only; one planted photo-caption message is worth adding to
    exercise the path.

## Verdict

**Gap found (G46).** Mostly additive contract surface: one enum, two nullable fields, and the
relay lane picks up forwards for free.
