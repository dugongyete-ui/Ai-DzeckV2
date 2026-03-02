#!/bin/bash
set -e

echo "=== Dzeck AI Build Script ==="
export PATH="/home/runner/workspace/.pythonlibs/bin:$PATH"

echo "[1/4] Installing backend Python dependencies..."
cd /home/runner/workspace/backend
pip install --user -q --disable-pip-version-check -r requirements.txt

echo "[2/4] Installing sandbox Python dependencies..."
cd /home/runner/workspace/sandbox
pip install --user -q --disable-pip-version-check -r requirements.txt

echo "[3/4] Installing frontend Node.js dependencies..."
cd /home/runner/workspace/frontend
npm install --silent

echo "[4/4] Building frontend for production..."
cd /home/runner/workspace/frontend
npm run build

echo "=== Build complete ==="
