#!/usr/bin/env bash
# Start uvicorn on :8000 and nginx on :2001 (no Docker).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
PROJECT="$(cd "$ROOT/.." && pwd)"
NGINX_DIR="$ROOT/nginx"

mkdir -p "$NGINX_DIR/logs" "$NGINX_DIR/tmp"

if ! command -v nginx >/dev/null 2>&1; then
  echo "nginx not found. Install it first, e.g.: brew install nginx"
  exit 1
fi

if [[ ! -d "$PROJECT/.venv" ]]; then
  echo "Missing .venv — create it in the project root first."
  exit 1
fi

MIME=""
for candidate in \
  /opt/homebrew/etc/nginx/mime.types \
  /usr/local/etc/nginx/mime.types \
  /etc/nginx/mime.types
do
  if [[ -f "$candidate" ]]; then
    MIME="$candidate"
    break
  fi
done

RUNTIME_CONF="$NGINX_DIR/tmp/nginx.runtime.conf"
if [[ -n "$MIME" ]]; then
  sed "s|include[[:space:]]\\+[^;]*mime.types;|include $MIME;|" \
    "$NGINX_DIR/nginx.conf" > "$RUNTIME_CONF"
else
  cp "$NGINX_DIR/nginx.conf" "$RUNTIME_CONF"
fi

cleanup() {
  if [[ -f "$NGINX_DIR/tmp/uvicorn.pid" ]]; then
    kill "$(cat "$NGINX_DIR/tmp/uvicorn.pid")" 2>/dev/null || true
    rm -f "$NGINX_DIR/tmp/uvicorn.pid"
  fi
}
trap cleanup EXIT

if ! curl -sf "http://127.0.0.1:8000/health" >/dev/null 2>&1; then
  echo "Starting uvicorn on 127.0.0.1:8000 ..."
  # shellcheck disable=SC1091
  source "$PROJECT/.venv/bin/activate"
  (
    cd "$PROJECT"
    nohup uvicorn keyword_generator_main.app:app --host 127.0.0.1 --port 8000 \
      > "$NGINX_DIR/logs/uvicorn.log" 2>&1 &
    echo $! > "$NGINX_DIR/tmp/uvicorn.pid"
  )
  sleep 2
else
  echo "uvicorn already running on 127.0.0.1:8000"
fi

echo "Starting nginx on port 2001 ..."
echo "App:      http://127.0.0.1:2001"
echo "Health:   http://127.0.0.1:2001/health"
echo "API docs: http://127.0.0.1:2001/docs"
exec nginx -p "$NGINX_DIR/" -c tmp/nginx.runtime.conf -g "daemon off;"
