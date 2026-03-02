#!/bin/bash
# =============================================================================
# Dzeck AI - Auto Setup Script untuk Replit
# Jalankan sekali: bash setup.sh
# =============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${GREEN}[OK]${NC} $1"; }
info() { echo -e "${BLUE}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
err() { echo -e "${RED}[ERROR]${NC} $1"; }

WORKSPACE=/home/runner/workspace
PIP="pip install --user -q --disable-pip-version-check"
export PATH="/home/runner/workspace/.pythonlibs/bin:$PATH"

echo ""
echo "=============================================="
echo "   Dzeck AI - Setup Script for Replit"
echo "=============================================="
echo ""

# ─── 1. PYTHON PACKAGES (Backend) ─────────────────────────────────────────────
info "Menginstall Python packages (backend)..."
cd $WORKSPACE/backend
$PIP -r requirements.txt 2>&1 | grep -E "(Successfully|ERROR|error|already)" || true
log "Backend Python packages selesai"

# ─── 2. PYTHON PACKAGES (Sandbox) ─────────────────────────────────────────────
info "Menginstall Python packages (sandbox)..."
cd $WORKSPACE/sandbox
$PIP -r requirements.txt 2>&1 | grep -E "(Successfully|ERROR|error|already)" || true
log "Sandbox Python packages selesai"

# ─── 3. NODE.JS PACKAGES (Frontend) ──────────────────────────────────────────
info "Menginstall Node.js packages (frontend)..."
cd $WORKSPACE/frontend
npm install --silent 2>&1 | tail -3 || true
log "Node.js packages selesai"

# ─── 4. CEK FILE .ENV ────────────────────────────────────────────────────────
info "Mengecek konfigurasi backend/.env..."

if [ ! -f "$WORKSPACE/backend/.env" ]; then
    warn "File backend/.env tidak ditemukan, membuat dari template..."
    cat > $WORKSPACE/backend/.env << 'EOF'
# LLM - Pollinations AI (API Key dari enter.pollinations.ai)
API_KEY=sk_z06J0JrX9oJyaDHB1lMBOBSZCNO0d4FG
API_BASE=https://text.pollinations.ai/v1
MODEL_NAME=openai-fast
TEMPERATURE=0.7
MAX_TOKENS=8000

# MongoDB Atlas
MONGODB_URI=mongodb+srv://galerizaki_db_user:wTkfzrqewY5qCxYG@cluster0.vmiek8b.mongodb.net/manus?retryWrites=true&w=majority
MONGODB_DATABASE=manus

# Redis Labs
REDIS_HOST=redis-16364.c279.us-central1-1.gce.cloud.redislabs.com
REDIS_PORT=16364
REDIS_DB=0
REDIS_PASSWORD=0W7ImuMIUrkUTF0wxYSkIWmc8MRjPrYX
REDIS_SSL=false

# Sandbox
SANDBOX_ADDRESS=127.0.0.1

# Search
SEARCH_PROVIDER=bing

# Auth
AUTH_PROVIDER=local
LOCAL_AUTH_EMAIL=admin@example.com
LOCAL_AUTH_PASSWORD=admin123

# JWT
JWT_SECRET_KEY=Namakamusiapa123
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

LOG_LEVEL=INFO
EOF
    log "File .env berhasil dibuat"
else
    log "File backend/.env sudah ada"
fi

# ─── 5. BERSIHKAN PORT LAMA ─────────────────────────────────────────────────
info "Membersihkan port yang mungkin masih digunakan..."

for PORT in 8082 8080 8000 5000 5900 5901 9222; do
    PID=$(lsof -ti :$PORT 2>/dev/null) || true
    if [ -n "$PID" ]; then
        kill -9 $PID 2>/dev/null || true
        warn "Killed process on port $PORT (PID: $PID)"
    fi
done

pkill -f "supervisord" 2>/dev/null || true
pkill -f "Xvfb :1" 2>/dev/null || true
pkill -f "x11vnc" 2>/dev/null || true
pkill -f "websockify" 2>/dev/null || true
pkill -f "uvicorn" 2>/dev/null || true
rm -f /tmp/supervisor.sock /tmp/supervisord.pid /tmp/.X1-lock /tmp/.X11-unix/X1 2>/dev/null || true

sleep 2
log "Port cleanup selesai"

# ─── 6. RANGKUMAN ───────────────────────────────────────────────────────────
echo ""
echo "=============================================="
echo "   Setup Selesai!"
echo "=============================================="
echo ""
echo "Cara menjalankan aplikasi:"
echo ""
echo "  Klik tombol Run di Replit (menjalankan semua workflows sekaligus)"
echo ""
echo "  Atau manual di terminal:"
echo "    bash start_sandbox.sh   (Terminal 1)"
echo "    bash start_backend.sh   (Terminal 2)"
echo "    bash start_frontend.sh  (Terminal 3)"
echo ""
echo "Workflows:"
echo "  - Sandbox          → port 8080 (dev) / 8082 (prod)"
echo "  - Backend          → port 8000"
echo "  - Start application → port 5000 (webview)"
echo ""
echo "Login credentials:"
echo "  Email    : admin@example.com"
echo "  Password : admin123"
echo ""
echo "API LLM:"
echo "  Provider : Pollinations AI (enter.pollinations.ai)"
echo "  Endpoint : https://text.pollinations.ai/v1"
echo "  Model    : openai-fast"
echo "  Dashboard: https://enter.pollinations.ai/ (lihat usage)"
echo ""
