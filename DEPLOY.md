# Deploy Guide

**Qdrant Cloud** (vectors) + **EC2** (LangGraph Server) + **Vercel** (chat UI).

| Layer | URL |
|-------|-----|
| Chat UI (prod) | https://jc-development-watch.vercel.app |
| LangGraph API | `http://<EIP>:8123` |
| Assistant ID | `jc_dev_watch` (`default` does not work on `langgraph up`) |

---

## Prerequisites

- AWS account
- [Packer](https://developer.hashicorp.com/packer/install) 1.14+
- [Terraform](https://developer.hashicorp.com/terraform/install) 1.5+
- API keys for OpenAI, Cohere, Tavily, LangSmith
- Qdrant Cloud cluster 

## 1. Pre-index Qdrant (do this locally first)

Vectors should exist **before** EC2 boots so startup skips the ~196-chunk embed pass.

```bash
# .env with QDRANT_URL + QDRANT_API_KEY (export or plain KEY=value both work)
uv run python scripts/index_corpus.py
```

Verify in Qdrant dashboard: collection `jc_agendas_2026` with ~196 points.

## 2. Local smoke tests

Prove backend and frontend together before any cloud spend:

```bash
# Component gates 
uv run python scripts/verify_components.py --step N   # 1–7

# Backend + embedded chat UI (local frontend)
uv run uvicorn app.main:app --reload --port 8000

# LangGraph API shape (what EC2 will run)
uv run langgraph dev
```

Hit `http://localhost:8000` 

## 3. Bake back end AMI 

The Packer template copies `app/`, `scripts/`, `data/`, `langgraph.json`, `pyproject.toml`,
`uv.lock`, `.env.example`, and `.dockerignore` into `/home/ubuntu/agent/`.

```bash
cd ami
packer init jc-development-watch-v1.0.0.pkr.hcl
packer build jc-development-watch-v1.0.0.pkr.hcl
# → note output AMI ID (e.g. ami-0e5358b6cc1b3819b)
```

**PDFs:** `data/agendas/` is gitignored. If PDFs exist on disk during `packer build`, they are
baked into the AMI. Otherwise `ingest.py` downloads from `data/inventory.json` URLs at runtime.

Copy the AMI ID into `provision/terraform.tfvars` (see `provision/terraform.tfvars.example`).

## 4. Terraform apply

```bash
cd provision
terraform init
terraform apply
```

Note outputs:

```bash
terraform output agent_api_public_ip
terraform output langgraph_api_url
terraform output vercel_env_hint
terraform output ssh_command
```

## 5. SSH bootstrap

```bash
ssh -i ~/.ssh/<key>.pem ubuntu@<EIP>
```

On the instance:

```bash
# 1. Create .env from example if needed
cp ~/agent/.env.example ~/agent/.env
vi ~/agent/.env  

# 2. Lock permissions
chmod 600 ~/agent/.env

# 3. Validate .env and start service
~/agent/scripts/ec2_start.sh
```

`check_env.sh` verifies the file exists and these keys have real values (not `...` placeholders):
`OPENAI_API_KEY`, `COHERE_API_KEY`, `TAVILY_API_KEY`, `QDRANT_URL`, `QDRANT_API_KEY`, `LANGSMITH_API_KEY`.

Recommended in `~/agent/.env`:

```
LANGCHAIN_TRACING_V2=false
```

Watch logs:

```bash
sudo journalctl -u jc-development-watch -f
```

First boot downloads agenda PDFs for BM25 (vectors come from Qdrant). Allow 2–5 minutes.

```bash
ls ~/agent/scripts/
test -x ~/agent/scripts/check_env.sh && echo OK
test -f ~/agent/data/inventory.json && echo OK
systemctl cat jc-development-watch | grep ExecStartPre
```

## 6. Verify API

```bash
curl -s http://<EIP>:8123/ok
# → {"ok":true}
```

LangGraph Platform docs: `http://<EIP>:8123/docs`

Confirm the assistant:

```bash
curl -s -X POST "http://<EIP>:8123/assistants/search" \
  -H "Content-Type: application/json" \
  -d '{"limit": 10}'
# → graph_id: "jc_dev_watch"
```

Test a run (replace thread UUID):

```bash
curl -s -X POST "http://<EIP>:8123/threads" \
  -H "Content-Type: application/json" \
  -d '{}'

curl -s -X POST "http://<EIP>:8123/threads/<thread_id>/runs/wait" \
  -H "Content-Type: application/json" \
  -d '{
    "assistant_id": "jc_dev_watch",
    "input": {"messages": [{"role": "user", "content": "What is case Z2026-0025?"}]}
  }'
```

## 7. Pre-Vercel chat UI (optional)

Before the Vercel frontend is wired, run the built-in FastAPI chat on the instance:

```bash
cd ~/agent
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open `http://<EIP>:8000` on phone/laptop. Add port 8000 to the security group if needed.

## 8. Vercel frontend

Create a **new** Vercel project — do not link to an unrelated existing project.

```bash
cd frontend
rm -rf .vercel                    # unlink any prior project
npx vercel                        # create jc-development-watch
```

Set **Root Directory** to `frontend` if importing via dashboard.

### Vercel environment variables

Set these **before** the first successful build (Production or All Environments):

| Variable | Value |
|----------|-------|
| `LANGGRAPH_API_URL` | `http://<EIP>:8123` |
| `LANGSMITH_API_KEY` | your LangSmith key |
| `NEXT_PUBLIC_ASSISTANT_ID` | `jc_dev_watch` |
| `NEXT_PUBLIC_API_URL` | `https://jc-development-watch.vercel.app/api` |

`LANGGRAPH_API_URL` is required at **build time** (the `/api` proxy initializes during `next build`).
`NEXT_PUBLIC_API_URL` must be an absolute URL on Vercel — relative `/api` causes *Invalid URL* in the browser SDK.

Deploy to production:

```bash
npx vercel --prod
```

Verify proxy from laptop:

```bash
curl -s https://jc-development-watch.vercel.app/api/ok
# → {"ok":true}
```

Phone/laptop smoke test: *What is case Z2026-0025?* — expect 240 Fairmount, six-story, 53 units, cited source.

TLS/nginx on 443 is a polish step — not required for functional testing.

## Network access

| Port | Service | SG rule |
|------|---------|---------|
| 8123 | LangGraph API | Open (default in `sg.tf`) |
| 8000 | FastAPI chat UI | Add manually if using pre-Vercel UI |
| 443/80 | TLS front-end | Open (future nginx) |
| 22 | SSH | Restrict `allowed_ssh_cidr` in tfvars |

## Teardown

```bash
cd provision && terraform destroy
```

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Build fails: `API URL is required` | Set `LANGGRAPH_API_URL` in Vercel, then redeploy |
| Browser: `Invalid URL` | Set `NEXT_PUBLIC_API_URL` to `https://<app>.vercel.app/api`, redeploy |
| `422 Invalid assistant: jc_dev_watch` … `simple_agent` | Wrong Vercel project or `LANGGRAPH_API_URL` pointing at a different backend |
| `default` assistant 404/422 | Use `jc_dev_watch` or UUID from `/assistants/search` |
| Service won't start | Run `~/agent/scripts/check_env.sh`; check `journalctl -u jc-development-watch` |
| Stale Docker compose | `~/agent/scripts/langgraph_stop.sh` then `ec2_start.sh` (or add `--recreate` to `langgraph_serve.sh`) |
| Slow first boot | Expected — PDF download + BM25 build; pre-index Qdrant to skip embed |
| Cohere rate limits | Retriever uses Cohere rerank; trial keys need pacing under load |
| RAGAS hangs | Set `LANGCHAIN_TRACING_V2=false` in `.env` |
| EIP changed after rebake | Update `LANGGRAPH_API_URL` in Vercel, redeploy |
