#!/bin/bash

# ╔════════════════════════════════════════════════════════════════════════════╗
# ║                   QUICK DEPLOY: LOCAL → VM                                ║
# ║             Push your LOCAL improvements to the VM                         ║
# ╚════════════════════════════════════════════════════════════════════════════╝

# Configuration
VM_IP="34.227.227.14"
VM_USER="ubuntu"
SSH_KEY="~/.ssh/metocean.pem"
VM_APP_DIR="/srv/metocean/app"
VM_STATIC_DIR="/srv/metocean/static"

echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║                 DEPLOYING LOCAL CODE TO VM                                ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "Target: $VM_USER@$VM_IP"
echo "SSH Key: $SSH_KEY"
echo ""

# Step 1: Backup current VM files
echo "📦 Step 1: Backing up current VM files..."
ssh -i "$SSH_KEY" "$VM_USER@$VM_IP" \
  "cd $VM_APP_DIR && tar -czf backup_$(date +%s).tar.gz api.py src/ 2>/dev/null && echo '✅ Backup created'" \
  || { echo "⚠️  Backup failed (continuing anyway)"; }

echo ""

# Step 2: Deploy api.py
echo "📤 Step 2: Uploading api.py..."
scp -i "$SSH_KEY" api.py "$VM_USER@$VM_IP:$VM_APP_DIR/" \
  && echo "✅ api.py uploaded" \
  || { echo "❌ Failed to upload api.py"; exit 1; }

echo ""

# Step 3: Deploy src/ directory
echo "📤 Step 3: Uploading src/ directory..."
scp -i "$SSH_KEY" -r src/* "$VM_USER@$VM_IP:$VM_APP_DIR/src/" \
  && echo "✅ src/ directory uploaded" \
  || { echo "❌ Failed to upload src/"; exit 1; }

echo ""

# Step 4: Deploy forecast.html
echo "📤 Step 4: Uploading forecast.html..."
scp -i "$SSH_KEY" forecast.html "$VM_USER@$VM_IP:$VM_STATIC_DIR/" \
  && echo "✅ forecast.html uploaded" \
  || { echo "❌ Failed to upload forecast.html"; exit 1; }

echo ""

# Step 5: Restart the service
echo "🔄 Step 5: Restarting metocean service..."
ssh -i "$SSH_KEY" "$VM_USER@$VM_IP" \
  "sudo systemctl restart metocean && sleep 2 && sudo systemctl status metocean" \
  && echo "✅ Service restarted" \
  || { echo "❌ Failed to restart service"; exit 1; }

echo ""

# Step 6: Verify deployment
echo "✔️  Step 6: Verifying deployment..."
sleep 2

echo ""
echo "Testing /health endpoint..."
curl -s -w "HTTP %{http_code}\n" https://$VM_IP/health \
  && echo "✅ Server is responding" \
  || echo "⚠️  Server not responding yet (may be starting up)"

echo ""
echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║                    ✅ DEPLOYMENT COMPLETE!                                ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "What was deployed:"
echo "  ✅ api.py (with admin-only invitation system)"
echo "  ✅ src/ directory (auth, db, models, email, etc.)"
echo "  ✅ forecast.html (with Nginx-compatible paths)"
echo ""
echo "VM has been updated with your LOCAL improvements!"
echo ""
echo "Next steps:"
echo "  1. Visit https://34.227.227.14 in your browser"
echo "  2. Log in with admin email: kamaluddeen.usman@utp.edu.my"
echo "  3. Use the admin dashboard to invite users"
echo ""

