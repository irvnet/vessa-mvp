resource "aws_security_group" "agent_api" {
  name        = "${local.project_name}-agent-api"
  description = "Ingress for LangGraph API, HTTPS, and SSH"
  vpc_id      = module.vpc.vpc_id

  ingress {
    description = "LangGraph API (langgraph up)"
    from_port   = 8123
    to_port     = 8123
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS from Vercel and public clients"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTP for redirect and certificate renewal"
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
    description = "Outbound package installs and model API calls"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${local.project_name}-agent-api-sg"
    Component   = "security"
    Service     = "agent-api"
    Description = "City Development Watch API edge security group"
  }
}
