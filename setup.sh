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

log()  { echo -e "${GREEN}[OK]${NC} $1"; }
info() { echo -e "${BLUE}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
err()  { echo -e "${RED}[ERROR]${NC} $1"; }

WORKSPACE=/home/runner/workspace
PIP="pip install --user -q --disable-pip-version-check"
export PATH="/home/runner/workspace/.pythonlibs/bin:$PATH"

echo ""
echo "=============================================="
echo "   Dzeck AI - Setup Script for Replit"
echo "=============================================="
echo ""

# ─── 1. PYTHON VERSION CHECK ──────────────────────────────────────────────────
info "Memeriksa Python version..."
PYTHON_VER=$(python3 --version 2>&1)
log "Python: $PYTHON_VER"

# ─── 2. PYTHON PACKAGES (Backend) ─────────────────────────────────────────────
info "Menginstall Python packages (backend)..."
cd $WORKSPACE/backend
$PIP -r requirements.txt 2>&1 | grep -E "(Successfully|ERROR|error)" || true
log "Backend Python packages selesai"

# ─── 3. VERIFY CRITICAL BACKEND PACKAGES ─────────────────────────────────────
info "Memverifikasi critical packages..."
python3 -c "
packages = {
    'fastapi': 'FastAPI',
    'uvicorn': 'Uvicorn',
    'motor': 'Motor (MongoDB async)',
    'redis': 'Redis',
    'openai': 'OpenAI SDK',
    'e2b': 'E2B Sandbox',
    'inngest': 'Inngest',
    'playwright': 'Playwright',
    'beanie': 'Beanie ODM',
    'mcp': 'MCP',
}
missing = []
for pkg, name in packages.items():
    try:
        __import__(pkg)
        print(f'  ✓ {name}')
    except ImportError:
        print(f'  ✗ {name} - MISSING')
        missing.append(pkg)
if missing:
    print(f'WARNING: Missing packages: {missing}')
else:
    print('All critical packages OK')
" 2>/dev/null || true
log "Package verification selesai"

# ─── 4. PYTHON PACKAGES (Sandbox) ─────────────────────────────────────────────
info "Menginstall Python packages (sandbox)..."
cd $WORKSPACE/sandbox
$PIP -r requirements.txt 2>&1 | grep -E "(Successfully|ERROR|error)" || true
log "Sandbox Python packages selesai"

# ─── 5. NODE.JS PACKAGES (Frontend) ──────────────────────────────────────────
info "Menginstall Node.js packages (frontend)..."
cd $WORKSPACE/frontend
npm install --silent 2>&1 | tail -3 || true
log "Node.js packages selesai"

# ─── 6. CEK FILE .ENV ────────────────────────────────────────────────────────
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

# Sandbox (default: Docker local sandbox)
SANDBOX_ADDRESS=127.0.0.1
SANDBOX_PROVIDER=docker

# E2B Cloud Sandbox (aktifkan dengan SANDBOX_PROVIDER=e2b)
# E2B_API_KEY=e2b_xxxxx  (sudah di-set di Replit Secrets)

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

# Inngest Background Jobs
# INNGEST_API_KEY=AfIYKlW4...  (sudah di-set di Replit Secrets)
# INNGEST_SIGNING_KEY=signkey-prod-...  (sudah di-set di Replit Secrets)
INNGEST_APP_ID=dzeck-ai-agent

LOG_LEVEL=INFO
EOF
    log "File .env berhasil dibuat"
else
    log "File backend/.env sudah ada"

    # Patch .env jika ada keys baru yang belum ada
    if ! grep -q "SANDBOX_PROVIDER" "$WORKSPACE/backend/.env"; then
        echo "" >> "$WORKSPACE/backend/.env"
        echo "# Sandbox provider (docker / e2b)" >> "$WORKSPACE/backend/.env"
        echo "SANDBOX_PROVIDER=docker" >> "$WORKSPACE/backend/.env"
        warn "Ditambahkan SANDBOX_PROVIDER=docker ke .env"
    fi
    if ! grep -q "INNGEST_APP_ID" "$WORKSPACE/backend/.env"; then
        echo "" >> "$WORKSPACE/backend/.env"
        echo "# Inngest" >> "$WORKSPACE/backend/.env"
        echo "INNGEST_APP_ID=dzeck-ai-agent" >> "$WORKSPACE/backend/.env"
        warn "Ditambahkan INNGEST_APP_ID ke .env"
    fi
fi

# ─── 7. CEK REPLIT SECRETS ───────────────────────────────────────────────────
info "Memeriksa Replit Secrets yang dibutuhkan..."
MISSING_SECRETS=()

check_secret() {
    local name=$1
    local required=$2
    if [ -n "${!name}" ]; then
        log "Secret $name: SET"
    elif [ "$required" = "required" ]; then
        err "Secret $name: MISSING (required)"
        MISSING_SECRETS+=("$name")
    else
        warn "Secret $name: not set (optional)"
    fi
}

check_secret "E2B_API_KEY" "optional"
check_secret "INNGEST_API_KEY" "optional"
check_secret "INNGEST_SIGNING_KEY" "optional"

if [ ${#MISSING_SECRETS[@]} -gt 0 ]; then
    warn "Beberapa required secrets belum di-set: ${MISSING_SECRETS[*]}"
    warn "Set di Replit: Tools → Secrets"
fi

# ─── 8. BERSIHKAN PORT LAMA ─────────────────────────────────────────────────
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

# ─── 9. RANGKUMAN ───────────────────────────────────────────────────────────
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
echo "Integrations (Replit Secrets):"
echo "  E2B_API_KEY        → Cloud sandbox (aktifkan: SANDBOX_PROVIDER=e2b di .env)"
echo "  INNGEST_API_KEY    → Background jobs endpoint: GET /api/inngest"
echo "  INNGEST_SIGNING_KEY → Inngest webhook security"
echo ""
echo "API LLM:"
echo "  Provider : Pollinations AI (enter.pollinations.ai)"
echo "  Endpoint : https://text.pollinations.ai/v1"
echo "  Model    : openai-fast"
echo "  Dashboard: https://enter.pollinations.ai/ (lihat usage)"
echo ""
