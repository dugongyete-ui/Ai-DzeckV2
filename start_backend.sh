#!/bin/bash
echo "=== Starting Backend API on port 8000 ==="
cd /home/runner/workspace/backend
export OPENSSL_CONF=/home/runner/workspace/backend/openssl_compat.cnf
export PATH="/home/runner/workspace/.pythonlibs/bin:$PATH"
/home/runner/workspace/.pythonlibs/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
