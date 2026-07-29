#!/bin/bash
# One-command backend update: SSH in, pull latest main, sync deps, restart.
# Run from anywhere in the repo.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
KEY="${VESSA_SSH_KEY:-$HOME/.ssh/asamples.pem}"
HOST="$(terraform -chdir="${REPO_ROOT}/provision-vessa" output -raw backend_public_ip)"

echo "==> Deploying to ubuntu@${HOST} ..."
ssh -i "${KEY}" "ubuntu@${HOST}" bash -s <<'REMOTE'
set -euo pipefail
cd ~/vessa
git pull --ff-only
/home/ubuntu/.local/bin/uv sync
sudo systemctl restart vessa
sudo systemctl --no-pager --lines=0 status vessa
REMOTE

URL="$(terraform -chdir="${REPO_ROOT}/provision-vessa" output -raw backend_url)"
echo "==> Health check (uvicorn needs a moment to bind after restart):"
for i in 1 2 3 4 5; do
  if curl -sf "${URL}/health"; then
    echo
    exit 0
  fi
  sleep 2
done
echo "Health check failed after retries — check: ssh -i ${KEY} ubuntu@${HOST} 'sudo journalctl -u vessa -n 50'" >&2
exit 1
