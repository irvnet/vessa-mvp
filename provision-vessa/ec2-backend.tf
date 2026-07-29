resource "aws_instance" "backend" {
  ami                    = data.aws_ami.ubuntu_2404_lts.id
  instance_type          = var.instance_type
  subnet_id              = module.vpc.public_subnets[0]
  vpc_security_group_ids = [aws_security_group.backend.id]
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

  user_data = templatefile("${path.module}/user-data.sh.tftpl", {
    github_repo_url  = var.github_repo_url
    openai_api_key   = var.openai_api_key
    backend_hostname = var.backend_domain
  })

  tags = {
    Name        = "${local.project_name}-backend"
    Component   = "compute"
    Service     = "backend"
    Description = "Vessa FastAPI backend (uvicorn + systemd, Caddy TLS front door)"
    OS          = "Ubuntu 24.04 LTS"
  }
}

resource "aws_eip" "backend" {
  domain = "vpc"

  tags = {
    Name        = "${local.project_name}-backend-eip"
    Component   = "network"
    Service     = "backend"
    Description = "Stable public endpoint for api.meetvessa.com"
  }
}

resource "aws_eip_association" "backend" {
  instance_id   = aws_instance.backend.id
  allocation_id = aws_eip.backend.id
}
