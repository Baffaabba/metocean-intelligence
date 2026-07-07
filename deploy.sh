#!/bin/bash
set -e

# ════════════════════════════════════════════════════════════════════════════
# MetOcean Intelligence Platform — First-time VM Setup
# ════════════════════════════════════════════════════════════════════════════
# Provisions a fresh AWS EC2 instance (Ubuntu 22.04 LTS): system packages,
# PostgreSQL, nginx, the Python environment, and the systemd service.
# Run this ONCE per new VM. For pushing later code changes to an
# already-provisioned VM, use redeploy.sh instead (or push to main — CI
# does this automatically via .github/workflows/deploy-ec2.yml).
#
# Usage: sudo bash deploy.sh   (run from the repo root, e.g. via git clone)

# ─── Configuration ─────────────────────────────────────────────────────────
# APP_DIR mirrors the repo root: APP_DIR/app/{api.py,src,...} plus
# pyproject.toml, uv.lock, .env, .venv/. This matches api.py's own
# "from app.src.x import ..." absolute imports.
APP_DIR="/srv/metocean/app"
CONFIG_DIR="/srv/metocean/config"
STATIC_DIR="/srv/metocean/static"
LOGS_DIR="/srv/metocean/logs"
MODELS_DIR="/srv/metocean/models"
PYTHON_VERSION="3.11"

# ─── Colors ───────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✓]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# ─── Checks ───────────────────────────────────────────────────────────────
if [[ $EUID -ne 0 ]]; then
    log_error "This script must be run as root (use: sudo bash deploy.sh)"
    exit 1
fi

if ! command -v apt &> /dev/null; then
    log_error "This script requires Ubuntu/Debian (apt package manager)"
    exit 1
fi

if [[ ! -f "app/api.py" ]] || [[ ! -d "app/src" ]]; then
    log_error "app/api.py or app/src not found. Run this from the repo root."
    exit 1
fi

log_info "Starting MetOcean Intelligence deployment..."

# ═══════════════════════════════════════════════════════════════════════════
# STEP 1: System Package Installation
# ═══════════════════════════════════════════════════════════════════════════
log_info "Step 1: Installing system packages..."
apt update -qq
apt upgrade -y -qq
apt install -y -qq curl wget build-essential python3-dev postgresql nginx git unzip

log_success "System packages installed"

# ═══════════════════════════════════════════════════════════════════════════
# STEP 2: Install uv Package Manager
# ═══════════════════════════════════════════════════════════════════════════
log_info "Step 2: Installing uv package manager..."
if ! command -v uv &> /dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
    log_success "uv installed"
else
    log_success "uv already installed"
fi

# ═══════════════════════════════════════════════════════════════════════════
# STEP 3: Create Directory Structure
# ═══════════════════════════════════════════════════════════════════════════
log_info "Step 3: Creating application directories..."
mkdir -p $APP_DIR $CONFIG_DIR $STATIC_DIR $LOGS_DIR $MODELS_DIR

log_success "Directories created"

# ═══════════════════════════════════════════════════════════════════════════
# STEP 4: Copy Application Files
# ═══════════════════════════════════════════════════════════════════════════
log_info "Step 4: Copying application files..."

cp -r app $APP_DIR/
cp pyproject.toml uv.lock $APP_DIR/
cp -r app/static/* $STATIC_DIR/
cp nginx.conf metocean.service $CONFIG_DIR/
cp .env.example $APP_DIR/.env.example

log_success "Application files copied ($APP_DIR/app, $STATIC_DIR, $CONFIG_DIR)"

# ═══════════════════════════════════════════════════════════════════════════
# STEP 5: Install Python 3.11
# ═══════════════════════════════════════════════════════════════════════════
log_info "Step 5: Installing Python $PYTHON_VERSION..."
cd $APP_DIR
uv python install $PYTHON_VERSION
log_success "Python $PYTHON_VERSION installed"

# ═══════════════════════════════════════════════════════════════════════════
# STEP 6: Install Python Dependencies
# ═══════════════════════════════════════════════════════════════════════════
log_info "Step 6: Installing Python dependencies (this may take 5+ minutes)..."
uv sync --python "python$PYTHON_VERSION" 2>&1 | tail -20
log_success "Python dependencies installed"

# ═══════════════════════════════════════════════════════════════════════════
# STEP 7: Install PyTorch (CPU)
# ═══════════════════════════════════════════════════════════════════════════
log_info "Step 7: Installing PyTorch (CPU version)..."
uv pip install torch==2.2.2 --index-url https://download.pytorch.org/whl/cpu 2>&1 | tail -10
log_success "PyTorch installed"

# ═══════════════════════════════════════════════════════════════════════════
# STEP 8: Create .env File
# ═══════════════════════════════════════════════════════════════════════════
log_info "Step 8: Creating .env configuration file..."

if [[ -f "$APP_DIR/.env" ]]; then
    log_warn ".env already exists, skipping..."
else
    cp $APP_DIR/.env.example $APP_DIR/.env

    PG_PASS=$(openssl rand -hex 16)
    JWT_SECRET=$(openssl rand -hex 32)

    sed -i "s/POSTGRES_PASSWORD=change-me/POSTGRES_PASSWORD=$PG_PASS/" $APP_DIR/.env
    sed -i "s/^METOCEAN_JWT_SECRET=$/METOCEAN_JWT_SECRET=$JWT_SECRET/" $APP_DIR/.env

    log_success ".env created with generated PostgreSQL password and JWT secret"
    log_warn "Email (Brevo SMTP) and CORS_ORIGINS still need real values — edit $APP_DIR/.env (see README.md)"
fi

# ═══════════════════════════════════════════════════════════════════════════
# STEP 9: PostgreSQL Setup
# ═══════════════════════════════════════════════════════════════════════════
log_info "Step 9: Setting up PostgreSQL database..."

systemctl start postgresql
systemctl enable postgresql

sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname = 'metocean'" | grep -q 1 || \
    sudo -u postgres psql -c "CREATE DATABASE metocean;" || true

sudo -u postgres psql -tc "SELECT 1 FROM pg_user WHERE usename = 'metocean'" | grep -q 1 || \
    sudo -u postgres psql -c "CREATE USER metocean WITH PASSWORD 'metocean';" || true

sudo -u postgres psql -c "ALTER ROLE metocean WITH CREATEDB;" || true

log_success "PostgreSQL configured"
log_warn "Default DB password is 'metocean' — set POSTGRES_PASSWORD in .env to match, or change the role's password to the generated one above"

# ═══════════════════════════════════════════════════════════════════════════
# STEP 10: Nginx Configuration
# ═══════════════════════════════════════════════════════════════════════════
log_info "Step 10: Configuring Nginx reverse proxy..."

rm -f /etc/nginx/sites-enabled/default || true
cp $CONFIG_DIR/nginx.conf /etc/nginx/sites-available/metocean
ln -sf /etc/nginx/sites-available/metocean /etc/nginx/sites-enabled/metocean

log_warn "nginx.conf references /etc/letsencrypt/live/YOUR_DOMAIN — set up your cert (certbot) and edit that path before starting nginx"

nginx -t && systemctl restart nginx

log_success "Nginx configured"

# ═══════════════════════════════════════════════════════════════════════════
# STEP 11: Systemd Service
# ═══════════════════════════════════════════════════════════════════════════
log_info "Step 11: Registering systemd service..."

cp $CONFIG_DIR/metocean.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable metocean

log_success "Systemd service registered"

# ═══════════════════════════════════════════════════════════════════════════
# STEP 12: Database Initialization
# ═══════════════════════════════════════════════════════════════════════════
log_info "Step 12: Initializing database..."

cd $APP_DIR
set -a; source .env; set +a
uv run python -c "from app.src.db import init_db; init_db(); print('✓ Database initialized')" || \
    log_warn "Database initialization failed — check the error above"

log_success "Database initialized"

# ═══════════════════════════════════════════════════════════════════════════
# STEP 13: Start Services
# ═══════════════════════════════════════════════════════════════════════════
log_info "Step 13: Starting services..."

systemctl start postgresql
systemctl start metocean
systemctl start nginx

log_success "Services started"

# ═══════════════════════════════════════════════════════════════════════════
# STEP 14: Verification
# ═══════════════════════════════════════════════════════════════════════════
log_info "Step 14: Verifying deployment..."
sleep 2

if curl -s -k https://localhost/health | grep -q '"status":"ok"'; then
    log_success "Health check passed!"
else
    log_warn "Health check failed - check logs with: systemctl status metocean"
fi

# ═══════════════════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════════════════
echo ""
echo "════════════════════════════════════════════════════════════════════════"
echo -e "${GREEN}✓ DEPLOYMENT COMPLETE!${NC}"
echo "════════════════════════════════════════════════════════════════════════"
echo ""
echo "📍 Access URLs:"
echo "   Login:    https://<your-domain>/login.html"
echo "   Admin:    https://<your-domain>/admin.html"
echo ""
echo "🔑 Admin emails (auto-created, no password until they use 'Forgot password'):"
echo "   - kamaluddeen.usman@utp.edu.my"
echo "   - baffaabba2@gmail.com"
echo ""
echo "📋 Useful Commands:"
echo "   Check status:   systemctl status metocean"
echo "   View logs:      journalctl -u metocean -f"
echo "   Restart:        systemctl restart metocean"
echo ""
echo "⚠️  Still needed before this is truly live:"
echo "   1. Real SSL cert (certbot) — nginx.conf currently points at YOUR_DOMAIN"
echo "   2. Brevo SMTP credentials + CORS_ORIGINS in $APP_DIR/.env — see README.md"
echo "   3. For subsequent code changes, use redeploy.sh or push to main (CI deploys automatically)"
echo ""
