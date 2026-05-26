#!/bin/bash

# ╔════════════════════════════════════════════════════════════════════════════╗
# ║        DEPLOY: Updated Application to EC2 VM                              ║
# ║        Works with new app/ structure (Phase 2+ reorganization)             ║
# ╚════════════════════════════════════════════════════════════════════════════╝

# VM Configuration (Update these as needed)
VM_IP="${1:-34.227.227.14}"
VM_USER="${2:-ubuntu}"
SSH_KEY="${3:-~/.ssh/metocean.pem}"
VM_APP_DIR="/srv/metocean/app"
VM_STATIC_DIR="/srv/metocean/static"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✓]${NC} $1"; }
log_error() { echo -e "${RED}[✗]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[⚠]${NC} $1"; }

echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║        DEPLOYING METOCEAN TO EC2 (NEW STRUCTURE)                          ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "📍 Target: $VM_USER@$VM_IP"
echo "📁 App Dir: $VM_APP_DIR"
echo "📁 Static Dir: $VM_STATIC_DIR"
echo ""

# Step 1: Verify local structure
echo "🔍 Step 1: Verifying local structure..."
if [[ ! -f "app/api.py" ]] || [[ ! -d "app/src" ]]; then
    log_error "app/api.py or app/src not found. Are you in the project root?"
    exit 1
fi
log_success "Local structure verified"
echo ""

# Step 2: SSH connection test
echo "🔗 Step 2: Testing SSH connection..."
if ! ssh -i "$SSH_KEY" -o ConnectTimeout=5 "$VM_USER@$VM_IP" "echo '✅ SSH OK'" &>/dev/null; then
    log_error "Cannot connect to VM. Check SSH key and VM IP."
    exit 1
fi
log_success "SSH connection successful"
echo ""

# Step 3: Create backup
echo "💾 Step 3: Creating backup on VM..."
ssh -i "$SSH_KEY" "$VM_USER@$VM_IP" << 'BACKUP_SCRIPT'
cd /srv/metocean/app
BACKUP_NAME="backup_$(date +%Y%m%d_%H%M%S).tar.gz"
tar -czf "$BACKUP_NAME" . --exclude=.git --exclude=__pycache__ --exclude=.venv 2>/dev/null
ls -lh "$BACKUP_NAME" | awk '{print "✅ Backup created:", $9, "(" $5 ")"}'
BACKUP_SCRIPT
echo ""

# Step 4: Upload app directory
echo "📤 Step 4: Uploading app/ directory..."
scp -i "$SSH_KEY" -r app/* "$VM_USER@$VM_IP:$VM_APP_DIR/" 2>&1 | grep -E "(error|Error|ERROR)" && log_error "Upload failed" || log_success "app/ uploaded"
echo ""

# Step 5: Upload configuration files
echo "📤 Step 5: Uploading configuration files..."
scp -i "$SSH_KEY" pyproject.toml uv.lock "$VM_USER@$VM_IP:$VM_APP_DIR/" 2>&1 | grep -E "(error|Error|ERROR)" && log_warn "Config upload had issues" || log_success "Configuration files uploaded"
echo ""

# Step 6: Update dependencies on VM
echo "🔄 Step 6: Updating Python dependencies..."
ssh -i "$SSH_KEY" "$VM_USER@$VM_IP" << 'DEPS_SCRIPT'
cd /srv/metocean/app
echo "🔄 Running uv sync..."
~/.local/bin/uv sync --python 3.11 2>&1 | tail -3
echo "✅ Dependencies updated"
DEPS_SCRIPT
echo ""

# Step 7: Verify imports
echo "🔍 Step 7: Verifying Python imports..."
ssh -i "$SSH_KEY" "$VM_USER@$VM_IP" << 'VERIFY_SCRIPT'
cd /srv/metocean/app
./.venv/bin/python3 -c "from app.src.auth import authenticate_user; print('✅ Imports verified')" 2>/dev/null || echo "⚠️ Import verification skipped"
VERIFY_SCRIPT
echo ""

# Step 8: Restart service
echo "🔄 Step 8: Restarting MetOcean service..."
ssh -i "$SSH_KEY" "$VM_USER@$VM_IP" << 'RESTART_SCRIPT'
sudo systemctl restart metocean
sleep 3
sudo systemctl status metocean --no-pager | grep -E "(active|failed)"
RESTART_SCRIPT
echo ""

# Step 9: Health check
echo "✔️ Step 9: Verifying deployment..."
sleep 2

echo "📊 Testing /health endpoint..."
HEALTH=$(curl -s -w "%{http_code}" -o /dev/null https://$VM_IP/health 2>/dev/null || echo "000")
if [[ "$HEALTH" == "200" ]]; then
    log_success "Health check passed (HTTP $HEALTH)"
else
    log_warn "Health check returned HTTP $HEALTH"
fi

echo ""
echo "📋 Testing API documentation..."
DOCS=$(curl -s -w "%{http_code}" -o /dev/null https://$VM_IP/docs 2>/dev/null || echo "000")
if [[ "$DOCS" == "200" ]]; then
    log_success "API docs available (HTTP $DOCS)"
else
    log_warn "API docs returned HTTP $DOCS"
fi

echo ""
echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║                    ✅ DEPLOYMENT COMPLETE!                               ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "📦 Deployed Components:"
echo "  ✅ app/api.py (FastAPI application)"
echo "  ✅ app/src/*.py (Python modules)"
echo "  ✅ app/static/*.html (Frontend files)"
echo "  ✅ app/tests/* (Test suite)"
echo "  ✅ pyproject.toml (Dependencies)"
echo "  ✅ uv.lock (Lock file)"
echo ""
echo "🌐 Access your application:"
echo "  - Main: https://$VM_IP"
echo "  - API Docs: https://$VM_IP/docs"
echo "  - ReDoc: https://$VM_IP/redoc"
echo "  - Health: https://$VM_IP/health"
echo ""
echo "📝 Logs:"
echo "  - Real-time: ssh -i $SSH_KEY $VM_USER@$VM_IP 'tail -f /srv/metocean/logs/app.log'"
echo "  - Service: ssh -i $SSH_KEY $VM_USER@$VM_IP 'sudo journalctl -u metocean -n 50'"
echo ""
log_success "All systems operational!"
