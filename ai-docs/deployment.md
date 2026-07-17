# Deployment

> Platform facts below were verified against vendor docs on **2026-07-17** (free tiers change often — re-check before committing money). Stack being deployed: Next.js frontend · FastAPI backend · Telegram bot · Postgres + pgvector · Claude API.

## The one architectural decision that shapes everything

**Telegram bot mode: long-polling for local dev, webhook for deploy.**

- *Long-polling* (`getUpdates`) needs no public URL — perfect for laptop dev and rehearsal — but requires an always-on process.
- *Webhook* mode turns the bot into a plain HTTPS route (`POST /telegram/webhook`) inside the FastAPI app. Telegram requires only TLS 1.2+ on ports 443/80/88/8443 (any PaaS URL qualifies) and authenticates via the `secret_token` → `X-Telegram-Bot-Api-Secret-Token` header.

Folding the bot into the API via webhook means **one deployable backend service** instead of API + worker — cheaper, simpler, fewer failure modes. Keep the scheduler (digest cron, staleness checks) as APScheduler inside the same process; that's why the backend still needs an always-on host (a sleeping free tier would miss the Monday digest).

## Recommended stack (demo day)

| Layer | Where | Tier | Cost | Why |
|---|---|---|---|---|
| Frontend (Next.js) | **Vercel** | Hobby | $0 | Natural Next.js home; free tier is generous (100GB transfer, 1M invocations); hackathon = non-commercial, so Hobby terms are fine. No card needed. |
| Backend (FastAPI + webhook bot + scheduler) | **Railway** | Hobby | $5/mo flat (includes $5 usage credit; a 0.5GB service burns ~$1/mo of it) | Always-on (no sleep), deploy-from-GitHub, needs a card. The $5 credit realistically covers API + DB for the hackathon month. |
| Database (Postgres + pgvector) | **Neon** free — or Railway's pgvector template to keep everything in one place | Free | $0 | 0.5GB storage, 100 compute-hrs/mo, pgvector included. Autosuspends after 5 min idle but **auto-wakes on query** (sub-second to a few seconds) — acceptable. |
| LLM | **Claude API** | pay-per-use | ~$1–5 for the whole hackathon | Batch extraction over the seed corpus + demo Q&A is thousands, not millions, of tokens. Keep the key server-side only. |

**Total: ~$5–10 for the entire hackathon.** That number goes in the pitch.

### Why not the obvious alternatives

- **Vercel for the backend** — no. Hobby functions hard-cap at 300s and are request-driven; no persistent process, so the scheduler dies and long-polling is impossible. Vercel hosts the FE only.
- **Supabase (free) for the DB** — tempting (500MB, pgvector, nice dashboard) but it **pauses after 7 days of inactivity and needs manual restore**. A quiet week before demo day = a dead database on stage. Only pick it if you'll be touching the DB daily anyway.
- **Render free tier** — web services sleep after 15 min idle with ~1 min cold start (a `/ask` in Telegram would time out feeling), background workers aren't free at all ($7/mo), and the free Postgres **self-destructs after 30 days**. Pass.
- **Fly.io** — no free tier for new orgs anymore; a small machine is ~$2–3/mo which is fine, but managed Postgres starts at $38/mo. Viable if you already have a legacy account; otherwise Railway is less friction.
- **AWS (RDS + ECS/EC2)** — the answer to "should the DB be on AWS?": **not for the hackathon**. Cheapest sensible RDS is ~$15+/mo plus VPC/IAM setup time that buys zero demo value. AWS is the right answer only if AIV later standardizes there; the repo's Docker Compose means migrating is `docker compose up` on an EC2 box.
- **Koyeb free** — deep-sleeps after 1h without traffic and that can't be disabled; card with $29 auth hold required. Pass.

### The self-hosted alternative (plays to your DevOps profile)

Everything on **one VPS with Docker Compose** — Hetzner CX22 (2 vCPU / 4GB) at €4.49/mo, or Oracle Cloud's Always-Free tier if you can stomach the signup friction and the recently-halved Ampere allowance (2 OCPU / 12GB as of ~June 2026, with idle-reclaim risk on free accounts).

- Compose file: `caddy` (auto-TLS) + `api` + `db` (postgres:17 + pgvector) + optionally the FE as a static export served by Caddy.
- Pros: full control, one bill, identical to local dev, great "runs anywhere" story.
- Cons: you own TLS/backups/updates; no free CDN for the FE; more moving parts to rehearse.

**Verdict:** Vercel + Railway + Neon for the hackathon (fastest, least ops); the Compose file you already maintain for local dev *is* the migration path to a VPS later.

## Environment & config

```
# backend (Railway service variables)
DATABASE_URL=postgres://...          # Neon or Railway PG
ANTHROPIC_API_KEY=sk-ant-...         # server-side only, never in FE
TELEGRAM_BOT_TOKEN=...               # from BotFather
TELEGRAM_WEBHOOK_SECRET=<random>     # checked against X-Telegram-Bot-Api-Secret-Token
APP_BASE_URL=https://<railway-app>   # used to call setWebhook on boot
BOT_MODE=webhook                     # local dev: polling

# frontend (Vercel)
NEXT_PUBLIC_API_URL=https://<railway-app>
API_SHARED_TOKEN=...                 # trivial auth between FE and API for the hackathon
```

- One `settings.py` (pydantic-settings) reads all of it; `.env.example` committed, `.env` git-ignored.
- On startup in webhook mode, the app calls `setWebhook(url=APP_BASE_URL/telegram/webhook, secret_token=...)` idempotently.

## CI/CD

Keep it boring:
- **Vercel**: GitHub integration, auto-deploy `frontend/` on push to `main` (preview deploys on PRs for free).
- **Railway**: GitHub integration, auto-deploy backend Dockerfile on push to `main`.
- **GitHub Actions**: one workflow — lint + `make eval` (extraction golden-set regression) on PR. The eval gate is the only CI that actually protects the demo.

## Post-hackathon handoff (the sustainability slide)

The NPO reality: no engineer on staff, ~$0 budget. The handoff story:
- Monthly cost: **Railway $5 + Neon $0 + Claude API <$5 ≈ under $10/month** at NPO scale (batch extraction, no per-message calls).
- Runs as **one container + one managed DB**; a semi-technical volunteer redeploys by clicking "Redeploy" in Railway.
- `HANDOFF.md` in the repo: how to rotate the bot token, where the API key lives, how to export all records to CSV/Notion (the memory outlives the tool).
- Escape hatch: `docker compose up` reproduces the entire system on any machine — no platform lock-in.

## Demo-day checklist

- [ ] Deploy frozen 24h before; no infra changes after.
- [ ] Ping the Neon DB the morning of (warm the autosuspend) and open the dashboard once (warm Vercel edge cache).
- [ ] Pre-run one digest + one `/ask` so responses are cached/verified.
- [ ] Fallback: local `docker compose up` + long-polling mode on the laptop, rehearsed — survives venue-wifi and platform outages alike.
- [ ] Phone hotspot as network fallback for the live Telegram beat.
