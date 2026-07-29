#!/bin/bash
# EC2 Gate C — validate .env, then start jc-development-watch.
set -euo pipefail

AGENT_HOME="${AGENT_HOME:-/home/ubuntu/agent}"
SERVICE_NAME="${SERVICE_NAME:-jc-development-watch}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export AGENT_HOME

echo "==> Checking ${AGENT_HOME}/.env ..."
"${SCRIPT_DIR}/check_env.sh"

echo "==> Enabling and starting ${SERVICE_NAME} ..."
sudo systemctl enable "${SERVICE_NAME}"
sudo systemctl restart "${SERVICE_NAME}"

echo "==> Service status:"
sudo systemctl --no-pager status "${SERVICE_NAME}" || true

echo ""
echo "==> Tail logs (Ctrl-C to exit):"
echo "    sudo journalctl -u ${SERVICE_NAME} -f"
echo ""
echo "==> Gate D — from your laptop:"
echo "    curl -s http://\$(curl -s ifconfig.me):8123/ok"
