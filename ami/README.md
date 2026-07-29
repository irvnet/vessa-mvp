# City Development Watch — Packer AMI

Builds **City Development Watch v1.0.0**: Ubuntu 24.04 LTS, Docker, pre-pulled LangGraph images, project at `~/agent`, and a `jc-development-watch` systemd unit (installed, not enabled).

Full deployment flow: [`DEPLOY.md`](../DEPLOY.md)

## Prerequisites

- [Packer](https://developer.hashicorp.com/packer/install) 1.14+
- AWS credentials with permission to launch/build AMIs
- EC2 key pair in your target region (default stack uses `us-east-1`)

## Build

```bash
cd ami
packer init jc-development-watch-v1.0.0.pkr.hcl
packer build jc-development-watch-v1.0.0.pkr.hcl
```

Note the output AMI ID and set `ami_id` in `provision/terraform.tfvars`.

## What `install.sh` does

1. Docker Engine + Compose plugin
2. Pre-pulls LangGraph stack images (`langchain/langgraph-api`, Redis, pgvector)
3. Installs `uv` for the `ubuntu` user
4. Runs `uv sync` in `~/agent` (after Packer copies the project)
5. Writes `/etc/systemd/system/jc-development-watch.service` — **`langgraph up`** on port 8123
6. Does **not** enable the service or fill secrets

## On the running instance

After `terraform apply`:

1. SSH in (see `terraform output ssh_command`)
2. `cp ~/agent/.env.example ~/agent/.env` then `vi ~/agent/.env` — API keys, plain `KEY=value` format
3. `chmod 600 ~/agent/.env`
4. `~/agent/scripts/ec2_start.sh` — validates `.env`, then starts the service
5. Confirm health: `curl http://localhost:8123/ok`

## Files

| File | Role |
|------|------|
| `jc-development-watch-v1.0.0.pkr.hcl` | Packer template (Ubuntu noble, tags, file provisioners) |
| `install.sh` | Host bootstrap run during AMI build |

## Tags (aligned with Terraform)

- `Project` = City Development Watch
- `ManagedBy` = packer
- `Version` = v1.0.0
