module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.21.0"

  name = "${local.project_name}-vpc"
  cidr = var.vpc_cidr

  azs            = [local.availability_zone]
  public_subnets = [var.public_subnet_cidr]

  enable_nat_gateway   = false
  enable_dns_hostnames = true
  enable_dns_support   = true

  map_public_ip_on_launch = true

  public_subnet_tags = {
    Name      = "${local.project_name}-public"
    Component = "network"
  }

  tags = merge(local.common_tags, {
    Component = "network"
  })

  vpc_tags = {
    Name        = "${local.project_name}-vpc"
    Description = "Isolated network for City Development Watch API workloads"
  }
}
