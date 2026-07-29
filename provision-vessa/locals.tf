locals {
  project_name  = "vessa"
  project_label = "Vessa"

  availability_zone = var.availability_zone != "" ? var.availability_zone : data.aws_availability_zones.available.names[0]

  common_tags = {
    Project     = local.project_label
    ManagedBy   = "terraform"
    Environment = var.environment
  }
}
