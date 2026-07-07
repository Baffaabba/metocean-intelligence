#!/bin/bash
# ══════════════════════════════════════════════════════════════════════════
# Quick redeploy: push local changes to an already-bootstrapped VM.
#
# For first-time VM setup, use deploy.sh instead. This script assumes
# PostgreSQL, nginx, and the systemd unit are already installed (deploy.sh
# has already been run once).
#
# Normally you don't need this — .github/workflows/deploy-ec2.yml does the
# same thing automatically on every push to main. This is for manual/
# emergency redeploys without going through CI.
#
# Usage: ./redeploy.sh [VM_IP] [VM_USER] [SSH_KEY_PATH]
# ══════════════════════════════════════════════════════════════════════════
set -e

VM_IP="${1:?Usage: ./redeploy.sh VM_IP [VM_USER] [SSH_KEY_PATH]}"
VM_USER="${2:-ubuntu}"
SSH_KEY="${3:-~/.ssh/metocean.pem}"

# Remote layout mirrors the repo root exactly: VM_ROOT/app/{api.py,src,static,tests},
# VM_ROOT/pyproject.toml, VM_ROOT/uv.lock — so `app.src.*` imports in api.py
# resolve the same way on the VM as they do locally. nginx serves static
# files from a separate copy at VM_STATIC_DIR (see nginx.conf).
VM_ROOT="/srv/metocean/app"
VM_STATIC_DIR="/srv/metocean/static"

RED='\033[0;31m'; GREEN='\033[0;32m'; BLUE='\033[0;34m'; YELLOW='\033[1;33m'; NC='\033[0m'
log_info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $1"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }

echo "Redeploying to $VM_USER@$VM_IP (key: $SSH_KEY)"
echo ""

log_info "Verifying local structure..."
if [[ ! -f "app/api.py" ]] || [[ ! -d "app/src" ]]; then
    log_error "app/api.py or app/src not found. Run this from the repo root."
    exit 1
fi
log_success "Local structure verified"

log_info "Testing SSH connection..."
if ! ssh -i "$SSH_KEY" -o ConnectTimeout=5 "$VM_USER@$VM_IP" "echo ok" &>/dev/null; then
    log_error "Cannot connect to VM. Check SSH key and VM IP."
    exit 1
fi
log_success "SSH connection OK"

log_info "Creating backup on VM..."
ssh -i "$SSH_KEY" "$VM_USER@$VM_IP" \
    "cd $VM_ROOT && tar -czf backup_\$(date +%Y%m%d_%H%M%S).tar.gz app pyproject.toml uv.lock --exclude=.venv --exclude=__pycache__ 2>/dev/null && echo backup ok" \
    || log_warn "Backup failed (continuing anyway)"

log_info "Uploading app/ (preserving structure)..."
scp -i "$SSH_KEY" -r app "$VM_USER@$VM_IP:$VM_ROOT/"
log_success "app/ uploaded"

log_info "Uploading pyproject.toml + uv.lock..."
scp -i "$SSH_KEY" pyproject.toml uv.lock "$VM_USER@$VM_IP:$VM_ROOT/"
log_success "Dependency files uploaded"

log_info "Syncing static files for nginx..."
ssh -i "$SSH_KEY" "$VM_USER@$VM_IP" "mkdir -p $VM_STATIC_DIR"
scp -i "$SSH_KEY" -r app/static/* "$VM_USER@$VM_IP:$VM_STATIC_DIR/"
log_success "Static files synced"

log_info "Updating Python dependencies on VM..."
ssh -i "$SSH_KEY" "$VM_USER@$VM_IP" "cd $VM_ROOT && ~/.local/bin/uv sync --python 3.11 2>&1 | tail -5"
log_success "Dependencies updated"

log_info "Restarting metocean service..."
ssh -i "$SSH_KEY" "$VM_USER@$VM_IP" "sudo systemctl restart metocean && sleep 3 && sudo systemctl status metocean --no-pager | grep -E '(Active|active)'"
log_success "Service restarted"

log_info "Verifying deployment..."
sleep 2
HEALTH=$(curl -s -o /dev/null -w "%{http_code}" "https://$VM_IP/health" 2>/dev/null || echo "000")
if [[ "$HEALTH" == "200" ]]; then
    log_success "Health check passed (HTTP $HEALTH)"
else
    log_warn "Health check returned HTTP $HEALTH — check: ssh -i $SSH_KEY $VM_USER@$VM_IP 'sudo journalctl -u metocean -n 50'"
fi

echo ""
log_success "Redeploy complete. Access: https://$VM_IP"
echo "Logs: ssh -i $SSH_KEY $VM_USER@$VM_IP 'tail -f /srv/metocean/logs/app.log'"
