# data-v3 — «Đêm nhạc Vì Trẻ Thơ» (live Telegram re-enactment corpus)

The second synthetic dataset — built to be **acted out for real**. Four real people
(Giang · Minh · Huy · Châu) type the scripted messages into two real Telegram groups,
and the live crawler must capture + extract them to the same end-state a replay of
`corpus.jsonl` produces. Longer and denser than data-v2: **280 messages, 30 decisions,
15 tasks, 4 signal chains, 10 distractors** across a 5-week storyline (17/06 → 21/07).

## Scenario

A 4-person volunteer crew organizes a charity music night ("Đêm nhạc Vì Trẻ Thơ",
20/07 at Nhà Văn Hóa Quận 3) raising funds for underprivileged children at Mái Ấm
Chợ Lớn. Giang = coordinator, Minh = lead Hậu cần, Huy = lead Truyền thông,
Châu = member (both teams).

Two Telegram groups, one project (ruling #13b — a project may own several groups):

| Group | Members | channel_name |
|---|---|---|
| **Hội AE** | all four | `hoi-ae` (186 msgs) |
| **BTC Core** | Giang, Minh, Huy | `btc-core` (94 msgs) |

The membership asymmetry is deliberate: budget and sensitive calls happen in Core and
get announced in Hội AE (→ corroboration / same-value handling), and Châu asks about
things already decided elsewhere.

## What the story exercises

- 4 `!decision` markers + 1 `!blocked` marker (deterministic lane)
- 12 reply-approvals (**actors must use Telegram's Reply feature** — script marks each)
- 2 supersessions (budget 30→35tr, xe 29→35 chỗ) + 1 **partial** supersession
  (D-29 changes only the open-time facet of D-01)
- 2 vetoes: one with nothing to restore (tờ rơi), one with **resurrection**
  (lineup v2 vetoed → lineup v1 restored)
- 1 windowed exception (exam-week fanpage policy — shadows, never supersedes)
- 1 delegation (Giang ủy quyền → member Châu's decision born effective)
- 1 relayed decision (Minh chuyển lời Giang → proposed → Giang self-confirms by reply)
- Weak-signal ledger: print vendor silent ×3 → **promoted with all 3 receipts**;
  sponsor silent ×2 → resolved before promotion (accumulates, never promotes)
- Task graph: 15 tasks, 1 canceled (→ dependent flips **needs_rewire**, then rewired),
  1 dependency chain (thiết kế → in ấn), multi-PIC, 1 task left open at corpus end
- 10 distractors that must extract to **nothing** (incl. the adversarial HDMI-cable one)
- 4 photo messages (media + caption), and **optional acts**: 2 reactions + 1 message
  edit (for when the crawler grows reaction/edit capture — core answer key never
  depends on them)

## Files

| File | What |
|---|---|
| `org.json` | seed: project, 2 teams, 2 groups, 4 users, 9 parties. **Placeholders**: fill real Telegram user ids + group chat ids before a live run |
| `corpus.jsonl` | canonical corpus (data-v2 schema), globally time-sorted, scripted timestamps |
| `script-hoi-ae.md`, `script-btc-core.md` | the human-actable scripts (generated FROM the corpus — never edit by hand; regenerate if the corpus changes) |
| `answer_key.json` | expected end-state: decision statuses, task folds, signal promotions, distractor inventory, live-run hero checks |

## Scene order (the two scripts interleave — follow this sequence)

| # | Group | Story date | Beat |
|---|---|---|---|
| 1 | Hội AE | 17/06 trưa | kickoff, phân công, 5 tasks |
| 2 | BTC Core | 17/06 tối | budget 30tr, mái ấm thụ hưởng |
| 3 | Hội AE | 19/06 | venue marker, lineup v1, gian hàng |
| 4 | BTC Core | 21/06 | âm thanh marker, phân bổ (reply-approve), !blocked giấy phép |
| 5 | Hội AE | 24/06 | GreenLeaf về, budget 30→35tr, vé tự nguyện |
| 6 | BTC Core | 28/06 | giấy phép xong (corroborate venue), xưởng in im lần 2 |
| 7 | Hội AE | 01/07 | veto tờ rơi, veto lineup v2 (resurrection), tuần thi window |
| 8 | BTC Core | 05/07 | promote blocker xưởng in → đổi xưởng, HỦY gian hàng (needs_rewire), ủy quyền Châu |
| 9 | Hội AE | 09–12/07 | công bố + quà top donor, Châu chốt áo (delegation), MC, phương án mưa |
| 10 | BTC Core | 17/07 | tài chính, dặn dò relay |
| 11 | Hội AE | 18–21/07 | relayed + self-confirm, NGÀY HỘI, đổi giờ mở cửa, tổng kết 42.35tr |

## Live re-enactment — how to run it

1. Create the two Telegram groups, add the bot (read-only), add the members per the
   table above. Bind chat ids + member Telegram ids into `org.json` placeholders.
2. Seed org (`python -m evermind.org.seed data-v3/org.json`), start the crawler.
3. Act the scripts **in scene order** (the ⏸ cues in each script mark hand-offs to the
   other group). Timing is free — order is not. Reply cues are mandatory; (( TÙY CHỌN ))
   acts are optional.
4. Compare the end-state against `answer_key.json` → `live_run_validation`: capture
   counts, then the hero checks. Match records to key entries **by text content**, not
   ids — live ids and timestamps will differ from the scripted ones.

Every date that matters ("20/07", "trước 25/06", "tuần 07-13/07") lives **inside message
text**, so a re-enactment compressed into one afternoon still extracts the same story.

## Replay use

`corpus.jsonl` replays through the standard pipeline exactly like data-v2 (channel names
`hoi-ae` / `btc-core` map via org.json). Not wired into CI/L0/eval — data-v2 remains the
CI fixture; promoting v3 into the eval harness is a separate decision.

**Hard-mode variant (optional):** delete Châu's row from `org.json` before a live run —
her first message then exercises provisional-user arrival (G44); her decisions must all
be born `proposed` until she's confirmed, and the delegation beat (D-24) becomes a
provisional-actor edge case. Only try once ING-6 provisional creation is wired.
