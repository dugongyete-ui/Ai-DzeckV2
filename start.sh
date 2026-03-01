#!/bin/bash
set -e

echo "=== Starting Dzeck AI ==="
echo "PORT env var: ${PORT:-not set, using 5000}"

# Kill any lingering processes from previous runs
fuser -k 8082/tcp 2>/dev/null || true
fuser -k 8080/tcp 2>/dev/null || true
fuser -k 8000/tcp 2>/dev/null || true
pkill -f "supervisord" 2>/dev/null || true
pkill -f "Xvfb :1" 2>/dev/null || true
pkill -f "x11vnc" 2>/dev/null || true
pkill -f "websockify" 2>/dev/null || true
pkill -f "uvicorn" 2>/dev/null || true
sleep 1

# ─── STEP 1: START FRONTEND FIRST ────────────────────────────────────────────
# Must start first so Replit health check (GET /) passes immediately
# Uses PORT env var injected by Replit, falls back to 5000
FRONTEND_PORT=${PORT:-5000}
echo "[1/3] Starting Frontend on port ${FRONTEND_PORT}..."
cd /home/runner/workspace/frontend

if [ -d "dist" ]; then
  echo "Serving production build via vite preview..."
  PORT=${FRONTEND_PORT} BACKEND_URL=http://localhost:8000 npx vite preview --host 0.0.0.0 --port ${FRONTEND_PORT} &
else
  echo "No production build found, using dev server..."
  PORT=${FRONTEND_PORT} BACKEND_URL=http://localhost:8000 npx vite --host 0.0.0.0 --port ${FRONTEND_PORT} &
fi
FRONTEND_PID=$!
echo "Frontend PID: $FRONTEND_PID"

# ─── STEP 2: START BACKEND ───────────────────────────────────────────────────
# SANDBOX_PORT=8082 so sandbox API doesn't conflict with PORT (8080) injected by Replit
echo "[2/3] Starting Backend on port 8000..."
cd /home/runner/workspace/backend
SANDBOX_PORT=8082 OPENSSL_CONF=/home/runner/workspace/backend/openssl_compat.cnf uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1 --timeout-keep-alive 75 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

# ─── STEP 3: START SANDBOX ───────────────────────────────────────────────────
# Uses supervisord-prod.conf where sandbox API runs on port 8082
echo "[3/3] Starting Sandbox service (supervisord + Xvfb + Chrome + VNC)..."
pkill -f "supervisord" 2>/dev/null || true
pkill -f "Xvfb :1" 2>/dev/null || true
pkill -f "x11vnc" 2>/dev/null || true
pkill -f "websockify" 2>/dev/null || true
pkill -f "chromium" 2>/dev/null || true
pkill -f "socat.*9222" 2>/dev/null || true

fuser -k 8082/tcp 2>/dev/null || true
fuser -k 5900/tcp 2>/dev/null || true
fuser -k 5901/tcp 2>/dev/null || true
fuser -k 9222/tcp 2>/dev/null || true
pkill -f "uvicorn.*8082" 2>/dev/null || true

sleep 2
rm -f /tmp/supervisor.sock /tmp/supervisord.pid /tmp/.X1-lock /tmp/.X11-unix/X1
sleep 1

cd /home/runner/workspace/sandbox
PYTHONPATH=/home/runner/workspace/sandbox supervisord -c /home/runner/workspace/sandbox/supervisord-prod.conf &

echo "=== All services started, keeping alive... ==="
wait $FRONTEND_PID
