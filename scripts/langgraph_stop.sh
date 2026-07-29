#!/bin/bash
# Stop LangGraph docker compose stack.
set -euo pipefail

ids="$(docker ps -q --filter 'name=langgraph' 2>/dev/null || true)"
if [[ -n "${ids}" ]]; then
  echo "==> Stopping langgraph containers..."
  docker stop ${ids}
fi

# compose projects started by langgraph CLI
while read -r project; do
  [[ -z "${project}" ]] && continue
  echo "==> docker compose -p ${project} down"
  docker compose -p "${project}" down --remove-orphans 2>/dev/null || true
done < <(docker compose ls --format json 2>/dev/null | python3 -c "
import sys, json
for line in sys.stdin:
    line = line.strip()
    if not line: continue
    try:
        o = json.loads(line)
        if 'langgraph' in o.get('Name','').lower() or 'agent' in o.get('Name','').lower():
            print(o['Name'])
    except Exception:
        pass
" 2>/dev/null || true)

echo "==> Done."
