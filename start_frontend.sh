#!/bin/bash
echo "=== Starting Frontend on port 5000 ==="
fuser -k 5000/tcp 2>/dev/null || true
sleep 1
cd /home/runner/workspace/frontend
PORT=5000 BACKEND_URL=http://localhost:8000 npx vite --port 5000 --host 0.0.0.0
