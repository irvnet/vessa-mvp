# City Development Watch — Terraform

Isolated VPC + single EC2 + Elastic IP for the self-hosted LangGraph agent API.

**Full deployment guide:** [`DEPLOY.md`](../DEPLOY.md)  
**AMI build:** [`ami/README.md`](../ami/README.md)

## What this stack creates

| Resource | Purpose |
|----------|---------|
| VPC `10.42.0.0/26` | Isolated network |
| Public subnet `10.42.0.0/28` | Agent host |
| EC2 + Elastic IP | Runs `langgraph up` via systemd |
| Security group | **8123 / 443 / 80 / 22** inbound by default |


Override in `terraform.tfvars`:

```hcl
vpc_cidr           = "10.44.0.0/26"
public_subnet_cidr = "10.44.0.0/28"
```

## Quick start

```bash
cd provision
terraform init
terraform apply
```

Defaults (region, AMI, SSH key, VPC CIDR): see `vars.tf` and `terraform.tfvars.example`.

Optional overrides:

```bash
cp terraform.tfvars.example terraform.tfvars
# e.g. allowed_ssh_cidr = "203.0.113.10/32"
# e.g. ami_id = "ami-xxxxxxxx"  # after Packer bake
```

## Outputs

```bash
terraform output agent_api_public_ip
terraform output langgraph_api_url
terraform output ssh_command
```

| Output | Use |
|--------|-----|
| `agent_api_public_ip` | EC2 public address |
| `langgraph_api_url` | `LANGGRAPH_API_URL` for Vercel |
| `vercel_env_hint` | Starting env vars for frontend |
| `ssh_command` | Fill `~/agent/.env`, start service |

After apply, continue at **DEPLOY.md → SSH bootstrap**.

## Tags

- `Project` = City Development Watch
- `ManagedBy` = terraform
- `Environment` = dev (default)

## Teardown

```bash
terraform destroy
```
