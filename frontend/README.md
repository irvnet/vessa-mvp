# City Development Watch — Frontend

Next.js chat UI streaming from the EC2 LangGraph API via `/api` proxy.

## Local dev

Backend must be running (`langgraph up` on EC2, or `langgraph dev` locally).

```bash
cd frontend
npm install
cp .env.local.example .env.local   # edit keys + URLs
npm run dev
```

Open `http://localhost:3000`.

### `.env.local`

| Variable | Example |
|----------|---------|
| `LANGGRAPH_API_URL` | `http://<EIP>` |
| `LANGSMITH_API_KEY` | `lsv2_pt_…` |
| `NEXT_PUBLIC_API_URL` | `http://localhost:3000/api` |
| `NEXT_PUBLIC_ASSISTANT_ID` | `jc_dev_watch` |

If `default` fails, fetch the assistant UUID:

```bash
curl -s -X POST "http://<EIP>/assistants/search" \
  -H "Content-Type: application/json" \
  -d '{"limit": 10}'
```

Set `NEXT_PUBLIC_ASSISTANT_ID` to the `assistant_id` for City Development Watch.

## Deploy to Vercel

```bash
npx vercel
npx vercel --prod
```

Set **Root Directory** to `frontend`.

### Vercel env vars

| Variable | Value |
|----------|-------|
| `LANGGRAPH_API_URL` | `http://<EIP>` |
| `LANGSMITH_API_KEY` | your LangSmith key |
| `NEXT_PUBLIC_API_URL` | `https://<your-app>.vercel.app/api` |
| `NEXT_PUBLIC_ASSISTANT_ID` | `jc_dev_watch` |

Redeploy after changing env vars.

See [`DEPLOY.md`](../DEPLOY.md) for full stack guide.
