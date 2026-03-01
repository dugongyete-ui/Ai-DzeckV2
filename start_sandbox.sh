#!/bin/bash
echo "=== Starting Sandbox service ==="

pkill -f "supervisord" 2>/dev/null || true
pkill -f "Xvfb :1" 2>/dev/null || true
pkill -f "x11vnc" 2>/dev/null || true
pkill -f "websockify" 2>/dev/null || true
pkill -f "chromium" 2>/dev/null || true
pkill -f "socat.*9222" 2>/dev/null || true

# Kill any orphaned processes holding sandbox ports
fuser -k 8080/tcp 2>/dev/null || true
fuser -k 5900/tcp 2>/dev/null || true
fuser -k 5901/tcp 2>/dev/null || true
fuser -k 9222/tcp 2>/dev/null || true

# Also kill any stale uvicorn on port 8080 (e.g., from testing runners)
pkill -f "uvicorn.*8080" 2>/dev/null || true

sleep 3

rm -f /tmp/supervisor.sock /tmp/supervisord.pid /tmp/.X1-lock /tmp/.X11-unix/X1

sleep 1

export PATH="/home/runner/workspace/.pythonlibs/bin:$PATH"
cd /home/runner/workspace/sandbox
PYTHONPATH=/home/runner/workspace/sandbox /home/runner/workspace/.pythonlibs/bin/supervisord -c /home/runner/workspace/sandbox/supervisord-replit.conf
