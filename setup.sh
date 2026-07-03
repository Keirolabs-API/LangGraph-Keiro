#!/usr/bin/env bash
# One-command install + setup for the Keiro x LangGraph integration.
# Creates a venv, installs deps, writes .env (prompts for keys), runs a self-check.
set -euo pipefail
cd "$(dirname "$0")"

PY="${PYTHON:-python3}"
VENV=".venv"

echo ">> venv ($VENV)"
[ -d "$VENV" ] || "$PY" -m venv "$VENV"
PIP="$VENV/bin/pip"; "$PIP" install --upgrade pip >/dev/null

echo ">> deps"
"$PIP" install langgraph langchain-mcp-adapters langchain-openai

[ -f .env ] || cp .env.example .env

ask_key() {  # ponytail: only prompts if the key is missing or blank
  local name="$1" prefix="$2" val
  if ! grep -q "^${name}=.\\+" .env; then
    read -rp ">> ${name} (starts with ${prefix}): " val
    [ -n "$val" ] || return 0
    if grep -q "^${name}=" .env; then
      sed -i "s|^${name}=.*|${name}=${val}|" .env
    else
      echo "${name}=${val}" >> .env
    fi
  fi
}
ask_key KEIRO_API_KEY "keiro_"
ask_key OPENAI_API_KEY "sk-"

echo ">> self-check"
"$VENV/bin/python" keiro-integration/keiro_langgraph.py check

cat <<EOF

Setup done. Ask the agent something:
  ./run.sh "latest news on X"
EOF