variable "aws_region" {
  description = "AWS region for the Vessa backend."
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment stage (dev, staging, production)."
  type        = string
  default     = "demo"
}

variable "vpc_cidr" {
  description = "Isolated VPC CIDR. Distinct from the jc-development-watch stack's 10.42/10.43 blocks."
  type        = string
  default     = "10.44.0.0/26"
}

variable "public_subnet_cidr" {
  description = "Public subnet for the backend host."
  type        = string
  default     = "10.44.0.0/28"
}

variable "availability_zone" {
  description = "AZ for compute. Leave empty to use the first available AZ in the region."
  type        = string
  default     = ""
}

variable "ssh_key_name" {
  description = "Existing EC2 key pair name in this region."
  type        = string
  default     = "asamples"
}

variable "allowed_ssh_cidr" {
  description = "CIDR allowed to SSH (use your public IP/32, not left open)."
  type        = string
  default     = "0.0.0.0/0"
}

variable "instance_type" {
  description = "EC2 size for the backend host. Vessa is a plain uvicorn process, no Docker/Redis/pgvector — lighter than the old stack."
  type        = string
  default     = "t3.small"
}

variable "root_volume_gb" {
  description = "Root disk size in GiB."
  type        = number
  default     = 20
}

variable "backend_domain" {
  description = "DNS name the backend will be reachable at (Caddy issues a real cert for this)."
  type        = string
  default     = "api.meetvessa.com"
}

variable "github_repo_url" {
  description = "Repo URL the backend clones on first boot. No default — must be set once the repo exists."
  type        = string
}

variable "openai_api_key" {
  description = "OpenAI API key, written into the backend's .env on first boot. Pass via TF_VAR_openai_api_key, never commit it."
  type        = string
  sensitive   = true
}
