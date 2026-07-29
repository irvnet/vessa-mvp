output "project" {
  description = "Project identity for this stack."
  value       = local.project_label
}

output "vpc_id" {
  description = "Isolated VPC hosting Vessa's infrastructure — fully separate from any other project."
  value       = module.vpc.vpc_id
}

output "vpc_cidr" {
  description = "VPC CIDR block."
  value       = module.vpc.vpc_cidr_block
}

output "backend_public_ip" {
  description = "Elastic IP for the backend host — point the api.meetvessa.com A record here (DNS-only, not proxied)."
  value       = aws_eip.backend.public_ip
}

output "backend_url" {
  description = "Backend's public HTTPS URL, once DNS + Caddy's cert are live."
  value       = "https://${var.backend_domain}"
}

output "ssh_command" {
  description = "SSH into the backend host."
  value       = "ssh -i ~/.ssh/${var.ssh_key_name}.pem ubuntu@${aws_eip.backend.public_ip}"
}

output "availability_zone" {
  description = "AZ where the backend host was placed."
  value       = local.availability_zone
}

output "instance_id" {
  description = "EC2 instance ID for the backend host."
  value       = aws_instance.backend.id
}
