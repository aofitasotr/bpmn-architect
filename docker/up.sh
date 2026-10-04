#!/bin/sh
set -e
NEED_GB=${COLIMA_MEMORY:-10}
CPUS=${COLIMA_CPU:-4}
if command -v colima >/dev/null 2>&1; then
  info=$(colima list -j 2>/dev/null | head -1)
  status=$(echo "$info" | python3 -c 'import json,sys; d=json.loads(sys.stdin.read() or "{}"); print(d.get("status",""))')
  have=$(echo "$info" | python3 -c 'import json,sys; d=json.loads(sys.stdin.read() or "{}"); print(d.get("memory",0)//(1024**3))')
  if [ "$status" != "Running" ]; then
    colima start --cpu "$CPUS" --memory "$NEED_GB"
  elif [ "$have" -lt "$NEED_GB" ]; then
    echo "colima has ${have} GB, need ${NEED_GB} GB, restarting"
    colima stop
    colima start --cpu "$CPUS" --memory "$NEED_GB"
  fi
fi
cd "$(dirname "$0")/.."
if docker compose version >/dev/null 2>&1; then
  exec docker compose up --build "$@"
fi
exec docker-compose up --build "$@"
