# Deploy Guide

**EC2** (FastAPI backend, behind Caddy for TLS) + **Vercel** (Next.js frontend).

| Layer | URL |
|-------|-----|
| Frontend (prod) | https://meetvessa.com |
| Backend API | https://api.meetvessa.com |

Backend is a plain `uv run uvicorn app.main:app` process — no Docker, no Redis, no vector DB. State is a single SQLite file (`data/vessa.db`) plus an in-process APScheduler background job (the proactive check-in loop), both of which need a persistent, always-on process — not serverless.

---

## Prerequisites

- AWS account
- [Terraform](https://developer.hashicorp.com/terraform/install) ≥ 1.5
- An existing EC2 key pair in your target region
- This repo pushed to a GitHub remote (the EC2 bootstrap does `git clone`)
- OpenAI API key
- A Vercel account
- Cloudflare access to the `meetvessa.com` DNS zone

## 1. Provision the backend

```bash
cd provision-vessa
cp terraform.tfvars.example terraform.tfvars   # set github_repo_url
export TF_VAR_openai_api_key=sk-...            # keep the real key out of any committed file
terraform init
terraform apply
```

This provisions an isolated VPC, one EC2 instance (Ubuntu 24.04 LTS), an Elastic IP, and a security group (443/80/22 only — port 8010 is never exposed publicly, Caddy is the only public entry point). First-boot `user-data` installs Caddy, `uv`, clones the repo, writes `.env`, runs `uv sync`, and starts the backend as a systemd service (`vessa.service`).

## 2. Point DNS at it

```bash
terraform output backend_public_ip
```
In Cloudflare, add an **A record**: `api.meetvessa.com` → that IP, **DNS-only (grey cloud, not proxied)**. Proxying it through Cloudflare would conflict with Caddy's own Let's Encrypt certificate issuance — DNS-only lets Caddy get a real cert directly.

## 3. Verify the backend

```bash
curl https://api.meetvessa.com/health
curl https://api.meetvessa.com/proof/health
```
(TLS cert issuance can take a minute or two after the DNS record propagates.)

## 4. Deploy the frontend

```bash
cd frontend
rm -rf .vercel
vercel link       # creates a fresh Vercel project — don't reuse an old one
```
In the Vercel dashboard: set `NEXT_PUBLIC_API_URL=https://api.meetvessa.com`, connect the `meetvessa.com` domain, then either `vercel --prod` for a manual first deploy, or connect the GitHub repo for auto-deploy on push (recommended — see the update workflow below).

## 5. Close the loop (one-time, manual)

The backend's `.env` starts with `ALLOWED_ORIGINS` defaulted to `http://localhost:3000` (the real Vercel URL doesn't exist yet at first boot, so Terraform can't set it). Once the frontend is live:

```bash
ssh -i ~/.ssh/<your-key>.pem ubuntu@<backend_public_ip>
vi ~/vessa/.env      # set ALLOWED_ORIGINS=https://meetvessa.com
sudo systemctl restart vessa
```

## Updating after the first deploy

- **Backend**: `./scripts/deploy.sh` — SSHes in, `git pull`s, `uv sync`s, restarts the service. One command.
- **Frontend**: `git push` to `main` — Vercel's GitHub integration auto-deploys.

## Troubleshooting

```bash
ssh -i ~/.ssh/<your-key>.pem ubuntu@<backend_public_ip>
sudo journalctl -u vessa -f     # backend logs
sudo journalctl -u caddy -f     # TLS/reverse-proxy logs
./scripts/check_env.sh          # validate .env directly
```

## Teardown

```bash
cd provision-vessa
terraform destroy
```
