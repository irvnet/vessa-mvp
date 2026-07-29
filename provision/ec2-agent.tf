resource "aws_instance" "agent_api" {
  ami                    = local.agent_ami_id
  instance_type          = var.instance_type
  subnet_id              = module.vpc.public_subnets[0]
  vpc_security_group_ids = [aws_security_group.agent_api.id]
  key_name               = var.ssh_key_name

  root_block_device {
    volume_type           = "gp3"
    volume_size           = var.root_volume_gb
    delete_on_termination = true
  }

  metadata_options {
    http_endpoint = "enabled"
    http_tokens   = "required"
  }

  tags = {
    Name        = "${local.project_name}-agent-api"
    Component   = "compute"
    Service     = "agent-api"
    Description = "LangGraph agent API for City Development Watch (frontend on Vercel)"
    OS          = "Ubuntu 24.04 LTS"
  }
}

resource "aws_eip" "agent_api" {
  domain = "vpc"

  tags = {
    Name        = "${local.project_name}-agent-api-eip"
    Component   = "network"
    Service     = "agent-api"
    Description = "Stable public endpoint for Vercel LANGGRAPH_API_URL"
  }
}

resource "aws_eip_association" "agent_api" {
  instance_id   = aws_instance.agent_api.id
  allocation_id = aws_eip.agent_api.id
}
