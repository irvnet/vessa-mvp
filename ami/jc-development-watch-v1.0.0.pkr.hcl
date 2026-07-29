
packer {
  required_plugins {
    amazon = {
      source  = "github.com/hashicorp/amazon"
      version = "1.8.1"
    }
  }
}

variable "aws_access_key" {
  type    = string
  default = "${env("AWS_ACCESS_KEY_ID")}"
}

variable "aws_secret_key" {
  type    = string
  default = "${env("AWS_SECRET_ACCESS_KEY")}"
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "environment" {
  type    = string
  default = "dev"
}

locals {
  project_name  = "jc-development-watch"
  project_label = "City Development Watch"
  ami_version   = "1.0.0"
  timestamp     = regex_replace(timestamp(), "[- TZ:]", "")

  common_tags = {
    Project     = local.project_label
    ManagedBy   = "packer"
    Environment = var.environment
    Component   = "compute"
    Service     = "agent-api"
    Version     = local.ami_version
    OS          = "Ubuntu 24.04 LTS"
    Description = "City Development Watch API — LangGraph Docker stack"
    Name        = "${local.project_name}-v${local.ami_version}"
  }
}

# Canonical Ubuntu 24.04 LTS (noble) — matches provision/data.tf
data "amazon-ami" "ubuntu_2404_lts" {
  access_key  = "${var.aws_access_key}"
  secret_key  = "${var.aws_secret_key}"
  region      = var.aws_region
  most_recent = true
  owners      = ["099720109477"]

  filters = {
    name                = "ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"
    root-device-type    = "ebs"
    virtualization-type = "hvm"
    architecture        = "x86_64"
  }
}

source "amazon-ebs" "jc_dev_watch" {
  access_key    = "${var.aws_access_key}"
  secret_key    = "${var.aws_secret_key}"
  region        = var.aws_region
  source_ami    = "${data.amazon-ami.ubuntu_2404_lts.id}"
  instance_type = "t3.large"
  ssh_username  = "ubuntu"

  ami_name = "${local.project_name}-v${local.ami_version}-${local.timestamp}"

  tags          = local.common_tags
  run_tags      = local.common_tags
  snapshot_tags = local.common_tags
}

build {
  sources = ["source.amazon-ebs.jc_dev_watch"]

  provisioner "shell" {
    inline = [
      "sudo mkdir -p /home/ubuntu/agent",
      "sudo chown ubuntu:ubuntu /home/ubuntu/agent",
    ]
  }

  provisioner "file" {
    source      = "../app"
    destination = "/home/ubuntu/agent/app"
  }

  provisioner "file" {
    source      = "../scripts"
    destination = "/home/ubuntu/agent/scripts"
  }

  provisioner "file" {
    source      = "../data"
    destination = "/home/ubuntu/agent/data"
  }

  provisioner "file" {
    sources = [
      "../langgraph.json",
      "../pyproject.toml",
      "../uv.lock",
      "../.env.example",
      "../.dockerignore",
    ]
    destination = "/home/ubuntu/agent/"
  }

  provisioner "shell" {
    script = "./install.sh"
  }
}
