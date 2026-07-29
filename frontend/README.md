# Vessa — Frontend

Next.js UI: companion chat, caregiver views (reminders/activity), and a `/proof` eval dashboard. Talks directly to Vessa's FastAPI backend over plain `fetch()` — no LangGraph proxy, no `/api` route.

## Local dev

Backend must be running (`uv run uvicorn app.main:app --reload --port 8010` from the repo root).

```bash
cd frontend
npm install
cp .env.local.example .env.local   # defaults to http://localhost:8010, edit if needed
npm run dev
```

Open `http://localhost:3000`.

### `.env.local`

| Variable | Example |
|----------|---------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8010` (local) or `https://api.meetvessa.com` (prod) |

## Deploy to Vercel

```bash
rm -rf .vercel
vercel link      # create a fresh project — don't reuse an old one
vercel --prod
```

Set **Root Directory** to `frontend`. In the Vercel dashboard, set `NEXT_PUBLIC_API_URL` to the deployed backend's URL, and connect the `meetvessa.com` domain.

Recommended: connect this repo's GitHub integration in Vercel instead of manual `vercel --prod` deploys — every push to `main` then auto-deploys.

See [`DEPLOY.md`](../DEPLOY.md) for the full stack guide.
