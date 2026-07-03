#!/usr/bin/env bash
# Loads .env and runs the Keiro ReAct agent on the given query.
# Costs Keiro credits (per API tool call) + LLM spend.
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -f .env ]; then
  echo "no .env found — run ./setup.sh first" >&2; exit 1
fi
set -a; . ./.env; set +a

exec .venv/bin/python keiro-integration/keiro_langgraph.py "$@"