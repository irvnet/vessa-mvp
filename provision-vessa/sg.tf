resource "aws_security_group" "backend" {
  name        = "${local.project_name}-backend"
  description = "Ingress for Caddy (HTTPS/HTTP) and SSH"
  vpc_id      = module.vpc.vpc_id

  ingress {
    description = "HTTPS (Caddy, terminates TLS for the real domain)"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTP (ACME challenge + redirect to HTTPS)"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "SSH administration"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.allowed_ssh_cidr]
  }

  egress {
    description = "Outbound package installs and OpenAI API calls"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${local.project_name}-backend-sg"
    Component   = "security"
    Service     = "backend"
    Description = "Vessa backend edge security group"
  }
}
