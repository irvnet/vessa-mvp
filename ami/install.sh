#!/bin/bash
# City Development Watch AMI v1.0.0 — host bootstrap for langgraph up (Docker)
set -euo pipefail

AGENT_HOME="/home/ubuntu/agent"
AGENT_USER="ubuntu"
LANGGRAPH_PORT="8123"
SERVICE_NAME="jc-development-watch"

echo "==> City Development Watch v1.0.0 (ami prep) install.sh"

# --- unattended apt ---
sudo sed -i "/#\$nrconf{restart} = 'i';/s/.*/\$nrconf{restart} = 'a';/" /etc/needrestart/needrestart.conf
echo 'debconf debconf/frontend select Noninteractive' | sudo debconf-set-selections

sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install -y ca-certificates curl gnupg lsb-release

# --- Docker Engine + Compose plugin (required for langgraph up) ---
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
https://download.docker.com/linux/ubuntu \
$(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y \
  docker-ce \
  docker-ce-cli \
  containerd.io \
  docker-buildx-plugin \
  docker-compose-plugin

sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker "${AGENT_USER}"

# --- pre-pull LangGraph stack images (faster first boot) ---
sudo docker pull langchain/langgraph-api:3.12
sudo docker pull redis:6
sudo docker pull pgvector/pgvector:pg16

# --- uv (runs langgraph CLI from ~/agent) ---
if ! sudo -u "${AGENT_USER}" test -x "/home/${AGENT_USER}/.local/bin/uv"; then
  sudo -u "${AGENT_USER}" bash -c 'curl -LsSf https://astral.sh/uv/install.sh | sh'
fi

sudo -u "${AGENT_USER}" mkdir -p "${AGENT_HOME}"

# --- agent app (runs after Packer file provisioner copies project) ---
if [[ -f "${AGENT_HOME}/langgraph.json" ]]; then
  echo "==> Configuring agent app in ${AGENT_HOME}"

  sudo chown -R "${AGENT_USER}:${AGENT_USER}" "${AGENT_HOME}"

  if [[ -f "${AGENT_HOME}/.env.example" && ! -f "${AGENT_HOME}/.env" ]]; then
    sudo -u "${AGENT_USER}" cp "${AGENT_HOME}/.env.example" "${AGENT_HOME}/.env"
    chmod 600 "${AGENT_HOME}/.env"
  fi

  sudo -u "${AGENT_USER}" bash -c "cd '${AGENT_HOME}' && /home/${AGENT_USER}/.local/bin/uv sync"

  if [[ -d "${AGENT_HOME}/scripts" ]]; then
    chmod +x "${AGENT_HOME}/scripts/"*.sh
  fi

  # systemd unit installed but not enabled — operator fills .env then runs scripts/ec2_start.sh
  sudo tee "/etc/systemd/system/${SERVICE_NAME}.service" > /dev/null <<EOF
[Unit]
Description=City Development Watch API (langgraph up)
Documentation=https://github.com/langchain-ai/langgraph
After=docker.service network-online.target
Wants=network-online.target
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
User=${AGENT_USER}
Group=docker
WorkingDirectory=${AGENT_HOME}
EnvironmentFile=-${AGENT_HOME}/.env
ExecStartPre=${AGENT_HOME}/scripts/check_env.sh
ExecStart=${AGENT_HOME}/scripts/langgraph_serve.sh
ExecStop=${AGENT_HOME}/scripts/langgraph_stop.sh
TimeoutStartSec=600

[Install]
WantedBy=multi-user.target
EOF

  sudo systemctl daemon-reload
  echo "==> After boot: vi ${AGENT_HOME}/.env, then: ${AGENT_HOME}/scripts/ec2_start.sh"
else
  echo "==> No ${AGENT_HOME}/langgraph.json yet — skipping app setup"
fi

echo "==> install.sh complete"
