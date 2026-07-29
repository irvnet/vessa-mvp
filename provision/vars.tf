variable "ami_id" {
  description = "AMI for the agent host. Empty uses latest Canonical Ubuntu 24.04 LTS. Set after Packer bake."
  type        = string
  default     = ""
}

variable "aws_region" {
  description = "AWS region for the City Development Watch backend."
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment stage (dev, staging, production)."
  type        = string
  default     = "dev"
}

variable "vpc_cidr" {
  description = "Isolated VPC CIDR (/26 fits up to ~10 instances)."
  type        = string
  default     = "10.42.0.0/26"
}

variable "public_subnet_cidr" {
  description = "Public subnet for the agent API host."
  type        = string
  default     = "10.42.0.0/28"
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
  description = "CIDR allowed to SSH (use your public IP/32 in production)."
  type        = string
  default     = "0.0.0.0/0"
}

variable "instance_type" {
  description = "EC2 size for LangGraph agent API and reverse proxy."
  type        = string
  default     = "t3.medium"
}

variable "root_volume_gb" {
  description = "Root disk size in GiB."
  type        = number
  default     = 30
}

variable "agent_api_domain" {
  description = "Optional DNS name for outputs. Empty uses the Elastic IP."
  type        = string
  default     = ""
}
