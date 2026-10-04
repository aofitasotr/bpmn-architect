#!/bin/sh
set -e
NEED_GB=${DOCKER_MEMORY_GB:-10}
CPUS=${COLIMA_CPU:-4}
cd "$(dirname "$0")/.."

if ! command -v docker >/dev/null 2>&1; then
  echo "docker is not installed: https://docs.docker.com/get-docker/"
  exit 1
fi

daemon_up() {
  docker info >/dev/null 2>&1
}

wait_daemon() {
  i=0
  while ! daemon_up; do
    i=$((i + 1))
    if [ "$i" -gt 60 ]; then
      echo "docker daemon did not start"
      exit 1
    fi
    sleep 2
  done
}

memory_gb() {
  bytes=$(docker info --format '{{.MemTotal}}' 2>/dev/null || echo 0)
  echo $((bytes / 1024 / 1024 / 1024))
}

if ! daemon_up; then
  if command -v colima >/dev/null 2>&1; then
    colima start --cpu "$CPUS" --memory "$NEED_GB"
  elif [ "$(uname -s)" = "Darwin" ]; then
    open -a Docker
  elif command -v systemctl >/dev/null 2>&1; then
    sudo systemctl start docker
  fi
  wait_daemon
fi

have=$(memory_gb)
if [ "$have" -lt "$NEED_GB" ]; then
  if command -v colima >/dev/null 2>&1 && colima status >/dev/null 2>&1; then
    echo "colima has ${have} GB, need ${NEED_GB} GB, restarting"
    colima stop
    colima start --cpu "$CPUS" --memory "$NEED_GB"
    wait_daemon
  else
    echo "warning: docker has ${have} GB of memory, ${NEED_GB} GB is recommended, the model may be killed (OOM)"
    echo "Docker Desktop: Settings > Resources > Memory"
    echo "WSL2: set memory=${NEED_GB}GB in %UserProfile%\\.wslconfig and run: wsl --shutdown"
  fi
fi

if docker compose version >/dev/null 2>&1; then
  exec docker compose up --build "$@"
fi
exec docker-compose up --build "$@"