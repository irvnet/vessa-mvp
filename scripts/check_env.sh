#!/bin/bash
# Validate ~/agent/.env before starting jc-development-watch.
# Used by scripts/ec2_start.sh and systemd ExecStartPre.
set -euo pipefail

AGENT_HOME="${AGENT_HOME:-/home/ubuntu/agent}"
ENV_FILE="${AGENT_HOME}/.env"

REQUIRED_KEYS=(
  OPENAI_API_KEY
  COHERE_API_KEY
  TAVILY_API_KEY
  QDRANT_URL
  QDRANT_API_KEY
  LANGSMITH_API_KEY
)

# Values that look like unfilled placeholders
is_placeholder() {
  local val="$1"
  [[ -z "${val}" ]] && return 0
  [[ "${val}" == "..." ]] && return 0
  [[ "${val}" =~ ^xxx+$ ]] && return 0
  [[ "${val}" =~ ^(changeme|REPLACE|TODO|your-|<.*>)$ ]] && return 0
  return 1
}

get_env_value() {
  local key="$1"
  local line val
  line="$(grep -E "^[[:space:]]*(export[[:space:]]+)?${key}=" "${ENV_FILE}" | tail -1 || true)"
  [[ -z "${line}" ]] && return 1
  val="${line#*=}"
  val="${val#"${val%%[![:space:]]*}"}"   # trim leading whitespace
  val="${val%"${val##*[![:space:]]}"}"   # trim trailing whitespace
  val="${val%\"}"; val="${val#\"}"       # strip double quotes
  val="${val%\'}"; val="${val#\'}"       # strip single quotes
  printf '%s' "${val}"
}

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "FAIL: ${ENV_FILE} not found." >&2
  echo "  cp ${AGENT_HOME}/.env.example ${ENV_FILE}" >&2
  echo "  vi ${ENV_FILE}" >&2
  exit 1
fi

if [[ ! -r "${ENV_FILE}" ]]; then
  echo "FAIL: ${ENV_FILE} is not readable." >&2
  exit 1
fi

missing=()
placeholder=()

for key in "${REQUIRED_KEYS[@]}"; do
  if ! val="$(get_env_value "${key}")"; then
    # LANGCHAIN_API_KEY satisfies LANGSMITH_API_KEY requirement
    if [[ "${key}" == "LANGSMITH_API_KEY" ]] && val="$(get_env_value "LANGCHAIN_API_KEY" 2>/dev/null || true)" && [[ -n "${val}" ]]; then
      continue
    fi
    missing+=("${key}")
    continue
  fi
  if is_placeholder "${val}"; then
    placeholder+=("${key}")
  fi
done

if ((${#missing[@]} > 0)); then
  echo "FAIL: missing required keys in ${ENV_FILE}:" >&2
  printf '  - %s\n' "${missing[@]}" >&2
  echo "  vi ${ENV_FILE}" >&2
  exit 1
fi

if ((${#placeholder[@]} > 0)); then
  echo "FAIL: placeholder values still set in ${ENV_FILE}:" >&2
  printf '  - %s\n' "${placeholder[@]}" >&2
  echo "  vi ${ENV_FILE}" >&2
  exit 1
fi

echo "OK: ${ENV_FILE} has all required keys with values."
