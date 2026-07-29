#!/bin/bash
# Start LangGraph stack detached and wait for healthy API (systemd-friendly).
set -euo pipefail

AGENT_HOME="${AGENT_HOME:-/home/ubuntu/agent}"
PORT="${LANGGRAPH_PORT:-8123}"

cd "${AGENT_HOME}"

echo "==> langgraph up --wait --no-pull (port ${PORT})"
/home/ubuntu/.local/bin/uv run langgraph up --port "${PORT}" --wait --no-pull

echo "==> LangGraph API should be listening on :${PORT}"
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' | grep -E 'langgraph|NAMES' || docker ps
