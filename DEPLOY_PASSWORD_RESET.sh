#!/bin/bash

# ╔════════════════════════════════════════════════════════════════════════════╗
# ║              DEPLOY: Password Recovery System to VM                        ║
# ╚════════════════════════════════════════════════════════════════════════════╝

VM_IP="34.227.227.14"
VM_USER="ubuntu"
SSH_KEY="~/.ssh/metocean.pem"
VM_APP_DIR="/srv/metocean/app"
VM_STATIC_DIR="/srv/metocean/static"

echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║            DEPLOYING PASSWORD RECOVERY SYSTEM TO VM                        ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "Target: $VM_USER@$VM_IP"
echo ""

# Step 1: Backup current VM files
echo "📦 Step 1: Backing up current VM files..."
ssh -i "$SSH_KEY" "$VM_USER@$VM_IP" \
  "cd $VM_APP_DIR && tar -czf backup_$(date +%s).tar.gz api.py src/ && echo '✅ Backup created'" \
  || { echo "⚠️  Backup failed (continuing anyway)"; }

echo ""

# Step 2: Deploy api.py
echo "📤 Step 2: Uploading api.py (with forgot-password & reset-password endpoints)..."
scp -i "$SSH_KEY" api.py "$VM_USER@$VM_IP:$VM_APP_DIR/" \
  && echo "✅ api.py uploaded" \
  || { echo "❌ Failed to upload api.py"; exit 1; }

echo ""

# Step 3: Deploy src/ directory
echo "📤 Step 3: Uploading src/ directory (with PasswordReset model & functions)..."
scp -i "$SSH_KEY" -r src/* "$VM_USER@$VM_IP:$VM_APP_DIR/src/" \
  && echo "✅ src/ directory uploaded" \
  || { echo "❌ Failed to upload src/"; exit 1; }

echo ""

# Step 4: Deploy HTML files
echo "📤 Step 4: Uploading HTML files (forgot-password, reset-password)..."
scp -i "$SSH_KEY" forgot-password.html reset-password.html "$VM_USER@$VM_IP:$VM_STATIC_DIR/" \
  && echo "✅ HTML files uploaded" \
  || { echo "❌ Failed to upload HTML files"; exit 1; }

echo ""

# Step 5: Deploy updated login.html (with Forgot Password link)
echo "📤 Step 5: Uploading updated login.html (with Forgot Password link)..."
scp -i "$SSH_KEY" login.html "$VM_USER@$VM_IP:$VM_STATIC_DIR/" \
  && echo "✅ login.html uploaded" \
  || { echo "❌ Failed to upload login.html"; exit 1; }

echo ""

# Step 6: Deploy updated forecast.html (LLM text removed)
echo "📤 Step 6: Uploading updated forecast.html (LLM text removed)..."
scp -i "$SSH_KEY" forecast.html "$VM_USER@$VM_IP:$VM_STATIC_DIR/" \
  && echo "✅ forecast.html uploaded" \
  || { echo "❌ Failed to upload forecast.html"; exit 1; }

echo ""

# Step 7: Restart the service
echo "🔄 Step 7: Restarting metocean service..."
ssh -i "$SSH_KEY" "$VM_USER@$VM_IP" \
  "sudo systemctl restart metocean && sleep 3 && sudo systemctl status metocean --no-pager" \
  && echo "✅ Service restarted" \
  || { echo "⚠️  Restart may have failed (check manually)"; }

echo ""

# Step 8: Verify deployment
echo "✔️  Step 8: Verifying deployment..."
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
echo "  ✅ api.py (with forgot-password & reset-password endpoints)"
echo "  ✅ src/ directory (with PasswordReset model & auth functions)"
echo "  ✅ forgot-password.html (new page for password recovery)"
echo "  ✅ reset-password.html (new page to set new password)"
echo "  ✅ login.html (updated with Forgot Password link)"
echo "  ✅ forecast.html (LLM text removed)"
echo ""
echo "Password recovery features:"
echo "  1. Visit https://34.227.227.14 → click 'Forgot password?'"
echo "  2. Enter email address → AWS SES sends reset link"
echo "  3. Click reset link → verify token & set new password"
echo "  4. Log in with new password"
echo ""
echo "Admin onboarding:"
echo "  1. Admin created with random password during init_db()"
echo "  2. Admin clicks 'Forgot password?' on first login"
echo "  3. Admin sets their own password via email link"
echo "  4. Admin can now log in and manage users"
echo ""

