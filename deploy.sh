#!/bin/bash
set -e

# ════════════════════════════════════════════════════════════════════════════
# MetOcean Intelligence Platform - VM Deployment Script
# ════════════════════════════════════════════════════════════════════════════
# Automated setup for AWS EC2 (Ubuntu 22.04 LTS)
# Usage: sudo bash deploy.sh

# ─── Configuration ─────────────────────────────────────────────────────────
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

# ─── Helper Functions ──────────────────────────────────────────────────────
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
mkdir -p $APP_DIR
mkdir -p $CONFIG_DIR
mkdir -p $STATIC_DIR
mkdir -p $LOGS_DIR
mkdir -p $MODELS_DIR

log_success "Directories created"

# ═══════════════════════════════════════════════════════════════════════════
# STEP 4: Copy Application Files (if deploy called from repo directory)
# ═══════════════════════════════════════════════════════════════════════════
log_info "Step 4: Checking for application files..."

if [[ -f "app/api.py" ]] && [[ -d "app/src" ]]; then
    log_info "Found application files in app/ directory (new structure)"
    
    # Copy Python source and static files
    cp app/api.py $APP_DIR/
    cp -r app/src $APP_DIR/
    cp -r app/static $STATIC_DIR/ 2>/dev/null || true
    cp app/pyproject.toml $APP_DIR/ 2>/dev/null || cp pyproject.toml $APP_DIR/ 2>/dev/null || true
    
    # Copy config files
    cp nginx.conf $CONFIG_DIR/
    cp metocean.service $CONFIG_DIR/
    cp metocean.env.example $APP_DIR/.env.example 2>/dev/null || cp .env.example $APP_DIR/.env.example 2>/dev/null || true
    
    log_success "Application files copied from app/ directory"
elif [[ -f "api.py" ]] && [[ -d "src" ]]; then
    log_info "Found application files in current directory (legacy structure)"
    
    # Copy Python source
    cp api.py $APP_DIR/
    cp -r src $APP_DIR/
    cp pyproject.toml $APP_DIR/
    
    # Copy static files
    cp *.html $STATIC_DIR/ 2>/dev/null || true
    cp *.csv $STATIC_DIR/ 2>/dev/null || true
    
    # Copy config files
    cp nginx.conf $CONFIG_DIR/
    cp metocean.service $CONFIG_DIR/
    cp metocean.env.example $APP_DIR/.env.example
    
    log_success "Application files copied from legacy structure"
elif [[ -d "metocean-backup" ]]; then
    log_info "Found metocean-backup directory"
    
    cp metocean-backup/app/* $APP_DIR/ 2>/dev/null || true
    cp metocean-backup/static/* $STATIC_DIR/ 2>/dev/null || true
    cp metocean-backup/config/* $CONFIG_DIR/ 2>/dev/null || true
    
    log_success "Files copied from backup"
else
    log_warn "Could not find application files automatically"
    log_info "Please ensure files are in /srv/metocean/ or provide them manually"
fi

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
# STEP 8: Create .env File (Interactive)
# ═══════════════════════════════════════════════════════════════════════════
log_info "Step 8: Creating .env configuration file..."

if [[ -f "$APP_DIR/.env" ]]; then
    log_warn ".env already exists, skipping..."
else
    cp $APP_DIR/.env.example $APP_DIR/.env
    
    # Generate secure values
    PG_PASS=$(openssl rand -hex 16)
    JWT_SECRET=$(openssl rand -hex 32)
    
    # Update values in .env
    sed -i "s/change-this-to-strong-password/$PG_PASS/" $APP_DIR/.env
    sed -i "s/your-super-secret-jwt-key/$JWT_SECRET/" $APP_DIR/.env
    
    log_success ".env created with generated secrets"
    
    # Prompt for AWS/domain settings
    echo ""
    log_info "Configure optional AWS SES email settings:"
    read -p "AWS Region (us-east-1): " AWS_REGION
    AWS_REGION=${AWS_REGION:-us-east-1}
    
    read -p "AWS Access Key ID (leave blank to skip): " AWS_KEY
    if [[ ! -z "$AWS_KEY" ]]; then
        read -p "AWS Secret Access Key: " AWS_SECRET
        read -p "Sender Email (noreply@your-domain.com): " SENDER_EMAIL
        read -p "App URL (https://your-domain.com): " APP_URL
        
        sed -i "s|us-east-1|$AWS_REGION|" $APP_DIR/.env
        sed -i "s|your-aws-access-key|$AWS_KEY|" $APP_DIR/.env
        sed -i "s|your-aws-secret-key|$AWS_SECRET|" $APP_DIR/.env
        sed -i "s|noreply@your-domain.com|$SENDER_EMAIL|" $APP_DIR/.env
        sed -i "s|https://your-domain.com|$APP_URL|" $APP_DIR/.env
        
        log_success "AWS configuration saved"
    fi
fi

# ═══════════════════════════════════════════════════════════════════════════
# STEP 9: PostgreSQL Setup
# ═══════════════════════════════════════════════════════════════════════════
log_info "Step 9: Setting up PostgreSQL database..."

systemctl start postgresql
systemctl enable postgresql

# Create database and user (if not exist)
sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname = 'metocean'" | grep -q 1 || \
    sudo -u postgres psql -c "CREATE DATABASE metocean;" || true

sudo -u postgres psql -tc "SELECT 1 FROM pg_user WHERE usename = 'metocean'" | grep -q 1 || \
    sudo -u postgres psql -c "CREATE USER metocean WITH PASSWORD 'metocean';" || true

sudo -u postgres psql -c "ALTER ROLE metocean WITH CREATEDB;" || true

log_success "PostgreSQL configured"

# ═══════════════════════════════════════════════════════════════════════════
# STEP 10: Nginx Configuration
# ═══════════════════════════════════════════════════════════════════════════
log_info "Step 10: Configuring Nginx reverse proxy..."

# Disable default site
rm -f /etc/nginx/sites-enabled/default || true

# Install custom config
if [[ -f "$CONFIG_DIR/nginx.conf" ]]; then
    cp $CONFIG_DIR/nginx.conf /etc/nginx/sites-available/metocean
else
    log_warn "nginx.conf not found, creating basic config..."
    # Create basic nginx config
    cat > /etc/nginx/sites-available/metocean << 'NGINX_EOF'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;

    # Redirect HTTP to HTTPS (update YOUR_DOMAIN)
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name _;

    # Self-signed certificate (replace with Let's Encrypt in production)
    ssl_certificate /etc/ssl/certs/metocean.crt;
    ssl_certificate_key /etc/ssl/private/metocean.key;

    client_max_body_size 50M;
    proxy_read_timeout 300s;

    # Static files
    location / {
        root /srv/metocean/static;
        try_files $uri /login.html;
    }

    # API proxy
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health check
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
    }
}
NGINX_EOF
fi

ln -sf /etc/nginx/sites-available/metocean /etc/nginx/sites-enabled/metocean

# Test config
nginx -t && systemctl restart nginx

log_success "Nginx configured"

# ═══════════════════════════════════════════════════════════════════════════
# STEP 11: Self-Signed Certificate (if not using Let's Encrypt)
# ═══════════════════════════════════════════════════════════════════════════
if [[ ! -f "/etc/ssl/certs/metocean.crt" ]]; then
    log_info "Step 11: Creating self-signed SSL certificate..."
    
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout /etc/ssl/private/metocean.key \
        -out /etc/ssl/certs/metocean.crt \
        -subj "/CN=metocean.local" 2>/dev/null
    
    chmod 600 /etc/ssl/private/metocean.key
    
    log_success "Self-signed certificate created"
    log_warn "For production: Install Let's Encrypt certificate (see README)"
fi

# ═══════════════════════════════════════════════════════════════════════════
# STEP 12: Systemd Service
# ═══════════════════════════════════════════════════════════════════════════
log_info "Step 12: Registering systemd service..."

if [[ -f "$CONFIG_DIR/metocean.service" ]]; then
    cp $CONFIG_DIR/metocean.service /etc/systemd/system/
else
    log_warn "metocean.service not found, creating..."
    cat > /etc/systemd/system/metocean.service << 'SERVICE_EOF'
[Unit]
Description=MetOcean Intelligence Platform
After=network.target postgresql.service

[Service]
Type=notify
User=www-data
WorkingDirectory=/srv/metocean/app
EnvironmentFile=/srv/metocean/app/.env
ExecStart=/root/.local/bin/uv run uvicorn api:app --host 127.0.0.1 --port 8000 --workers 2
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE_EOF
fi

systemctl daemon-reload
systemctl enable metocean
log_success "Systemd service registered"

# ═══════════════════════════════════════════════════════════════════════════
# STEP 13: Database Initialization
# ═══════════════════════════════════════════════════════════════════════════
log_info "Step 13: Initializing database..."

cd $APP_DIR
export $(cat .env | xargs)
uv run python -c "from src.db import init_db; init_db(); print('✓ Database initialized')" || \
    log_warn "Database initialization - check logs if issues"

log_success "Database initialized"

# ═══════════════════════════════════════════════════════════════════════════
# STEP 14: Start Services
# ═══════════════════════════════════════════════════════════════════════════
log_info "Step 14: Starting services..."

systemctl start postgresql
systemctl start metocean
systemctl start nginx

log_success "Services started"

# ═══════════════════════════════════════════════════════════════════════════
# STEP 15: Verification
# ═══════════════════════════════════════════════════════════════════════════
log_info "Step 15: Verifying deployment..."

sleep 2

if curl -s -k https://localhost/health | grep -q '"status":"healthy"'; then
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
echo "   Login:    https://localhost/login.html"
echo "   Admin:    https://localhost/admin.html"
echo "   API:      https://localhost/docs"
echo ""
echo "🔑 Admin Emails (auto-created):"
echo "   - kamaluddeen.usman@utp.edu.my"
echo "   - baffaabba2@gmail.com"
echo ""
echo "📋 Useful Commands:"
echo "   Check status:   systemctl status metocean"
echo "   View logs:      tail -f /srv/metocean/logs/app.log"
echo "   Start service:  systemctl start metocean"
echo "   Stop service:   systemctl stop metocean"
echo ""
echo "📖 For production SSL setup, see README.md"
echo ""
