# GitHub Actions Setup Guide

## Complete Instructions for CI/CD Automation

---

## 📋 Prerequisites

- ✅ GitHub account (baffaabba2@gmail.com)
- ✅ Repository access to `metocean-intelligence`
- ✅ SSH key for VM: `~/.ssh/metocean.pem`
- ✅ VM IP: `34.227.227.14`
- ✅ VM User: `ubuntu`

---

## 🔐 Step 1: Configure GitHub Secrets

GitHub Secrets store sensitive data (SSH keys, credentials) securely.

### 1.1 Access Secret Settings

1. Go to: `https://github.com/baffaabba2/metocean-intelligence`
2. Click: **Settings** → **Secrets and variables** → **Actions**
3. Click: **New repository secret** button

### 1.2 Add SSH_PRIVATE_KEY

**What**: Your private SSH key from `~/.ssh/metocean.pem`

**Steps**:
```bash
# 1. Get key content
cat ~/.ssh/metocean.pem

# 2. Copy the entire output (including BEGIN/END lines)
```

**In GitHub**:
- Name: `SSH_PRIVATE_KEY`
- Value: Paste entire key content
- Click: **Add secret**

**Verify**:
```bash
# List your secrets
gh secret list

# Should show: SSH_PRIVATE_KEY
```

### 1.3 Add VM_IP

**Name**: `VM_IP`  
**Value**: `34.227.227.14`  
**Click**: **Add secret**

### 1.4 Add VM_USER

**Name**: `VM_USER`  
**Value**: `ubuntu`  
**Click**: **Add secret**

### 1.5 (Optional) Add AWS Credentials

**When**: When you have AWS SES set up for emails

**Names**:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `SENDER_EMAIL`

**How to get AWS credentials**:
```bash
# From AWS Console → IAM → Users → Security credentials
# Create access key (keep secret!)
```

### Secrets Checklist

```
☑ SSH_PRIVATE_KEY         (paste full key)
☑ VM_IP                   (34.227.227.14)
☑ VM_USER                 (ubuntu)
☐ AWS_ACCESS_KEY_ID       (when ready)
☐ AWS_SECRET_ACCESS_KEY   (when ready)
☐ SENDER_EMAIL            (when ready)
```

---

## 📤 Step 2: Push Workflows to Repository

### 2.1 Verify Workflow Files

Check workflows are in correct location:

```bash
ls -la .github/workflows/

# Should show:
# tests.yml         (testing workflow)
# code-quality.yml  (linting & quality)
# deploy-ec2.yml    (deployment workflow)
```

### 2.2 Commit Workflows

```bash
# Add all workflow files
git add .github/workflows/

# Commit
git commit -m "Add: GitHub Actions CI/CD workflows

- tests.yml: Multi-version Python testing with coverage
- code-quality.yml: Linting and code analysis
- deploy-ec2.yml: Automated deployment to EC2"

# Push to repository
git push origin main
```

### 2.3 Verify Workflows Activated

1. Go to: `https://github.com/baffaabba2/metocean-intelligence/actions`
2. Should see workflows listed:
   - ✅ Tests & Coverage
   - ✅ Code Quality & Linting
   - ✅ Deploy to EC2

---

## 🧪 Step 3: Run First Test Workflow

### 3.1 Manual Trigger

```bash
# Trigger test workflow
gh workflow run tests.yml --ref main

# View status
gh run list --workflow tests.yml --limit 1

# View detailed output
gh run view <run-id> --log
```

**Or via GitHub UI**:
1. Go to: **Actions** → **Tests & Coverage**
2. Click: **Run workflow** → **Run workflow** button
3. Select branch: `main`

### 3.2 What to Expect

**Initial Run** (~5-10 minutes):
```
✅ Setup Python 3.10
✅ Install dependencies
✅ Run unit tests       (20-30 tests)
✅ Run integration tests (50-60 tests)
✅ Generate coverage report
✅ Upload to Codecov
✅ All checks passed!
```

**In PR Comments**:
```
## Test Results
- Python 3.10: ✅ PASSED
- Python 3.11: ✅ PASSED
- Coverage: 85%
- Type Check: ✅ PASSED
```

### 3.3 Check Results

```bash
# View workflow runs
gh run list --workflow tests.yml

# View specific run details
gh run view <run-id>

# View logs
gh run view <run-id> --log

# Cancel running workflow
gh run cancel <run-id>
```

---

## 🚀 Step 4: Deploy to EC2

### 4.1 First Deployment via GitHub Actions

```bash
# Push to main (triggers deployment)
git add .
git commit -m "Deploy: New features for production"
git push origin main

# Or manually trigger
gh workflow run deploy-ec2.yml --ref main
```

### 4.2 Monitor Deployment

**In GitHub**:
1. Go to: **Actions** → **Deploy to EC2**
2. Click latest run
3. Watch logs in real-time:
   - SSH connection setup
   - Backup creation
   - File upload
   - Dependency update
   - Service restart
   - Health verification

**Example Log Output**:
```
🔧 Configure SSH
✅ SSH connection successful

💾 Create backup on VM
✅ Backup created: backup_20240526_143022.tar.gz (245M)

📤 Upload application files
✅ app/ uploaded
✅ Configuration files uploaded

🔄 Update application on VM
🔄 Running uv sync...
✅ Dependencies updated

🔄 Restart service
✅ metocean service restarted

✔️ Verify deployment
✅ Health check passed (HTTP 200)
✅ API docs available (HTTP 200)

✅ DEPLOYMENT COMPLETE!
```

### 4.3 Verify Deployed Application

```bash
# Test health endpoint
curl https://34.227.227.14/health

# Test API docs
curl https://34.227.227.14/docs

# SSH to verify service running
ssh -i ~/.ssh/metocean.pem ubuntu@34.227.227.14
sudo systemctl status metocean

# View logs
tail -f /srv/metocean/logs/app.log
```

---

## 🔄 Step 5: Set Up Branch Protection

Enforce testing before merging to main:

### 5.1 Enable Branch Protection

1. Go to: **Settings** → **Branches**
2. Click: **Add rule**
3. Branch name pattern: `main`
4. Check boxes:
   - ✅ Require a pull request before merging
   - ✅ Require status checks to pass before merging
   - ✅ Require branches to be up to date before merging
   - ✅ Include administrators

### 5.2 Select Required Status Checks

1. Select: `Tests & Coverage` workflow
2. Select: `Code Quality & Linting` workflow
3. Click: **Create**

### 5.3 Test Branch Protection

```bash
# Create test branch
git checkout -b test-feature
echo "test" > test.txt
git add .
git commit -m "Test: feature branch"
git push origin test-feature

# Create pull request
gh pr create --title "Test: PR workflow" --body "Testing branch protection"

# Should show required checks:
# - Tests & Coverage ❌ (pending)
# - Code Quality & Linting ❌ (pending)
# - Deploy to EC2 ⏭️ (not required)
```

---

## 📊 Step 6: Monitor Workflows

### 6.1 View All Workflow Runs

```bash
# List recent runs
gh run list --limit 10

# List runs by workflow
gh run list --workflow tests.yml

# List runs by status
gh run list --status success
gh run list --status failure
```

### 6.2 View Workflow Details

```bash
# Get comprehensive info
gh run view <run-id>

# View specific job
gh run view <run-id> --job <job-id>

# View logs
gh run view <run-id> --log

# Download logs
gh run download <run-id>
```

### 6.3 Set Up Email Notifications

1. Go to: **Settings** → **Notifications**
2. Check: **GitHub Actions**
3. Select: **Send notifications for**
   - ✅ Workflow runs
   - ✅ Job failures
4. Click: **Save**

---

## 🛠️ Step 7: Troubleshooting Workflows

### Issue 1: Tests Failing

**Check**:
```bash
# View failure details
gh run view <run-id> --log

# Look for error message

# Common issues:
# - Import error: Check app.src.* paths
# - Database error: Check DATABASE_URL
# - Timeout: Increase timeout in workflow
```

**Fix**:
```bash
# Run tests locally to debug
pytest app/tests/ -v

# Once fixed, commit and push
git push origin main
```

### Issue 2: SSH Connection Failed

**Error**: `Permission denied (publickey)`

**Fix**:
1. Verify SSH key in GitHub secrets:
   ```bash
   # Check key format
   cat ~/.ssh/metocean.pem | head -5
   # Should show: -----BEGIN ... PRIVATE KEY-----
   ```

2. Verify VM security group allows SSH from GitHub:
   - AWS Console → EC2 → Security Groups
   - Inbound Rules: SSH (22) from 0.0.0.0/0

3. Verify key permissions on VM:
   ```bash
   ssh ubuntu@34.227.227.14
   ls -la ~/.ssh/  # Should show 600 permissions
   ```

### Issue 3: Deployment Failed / Rollback Triggered

**Check logs**:
```bash
# View deployment logs
gh run view <deploy-run-id> --log

# Check VM status
ssh ubuntu@34.227.227.14 'sudo systemctl status metocean'

# View app logs
ssh ubuntu@34.227.227.14 'tail -100 /srv/metocean/logs/app.log'
```

**Manual Rollback**:
```bash
ssh ubuntu@34.227.227.14
cd /srv/metocean/app

# List backups
ls -lh backup_*.tar.gz

# Restore latest
LATEST=$(ls -t backup_*.tar.gz | head -1)
tar -xzf $LATEST

# Restart service
sudo systemctl restart metocean
```

### Issue 4: Coverage Below Threshold

**Message**: `Coverage is 78%, but 80% required`

**Fix**:
```bash
# Add more tests
pytest app/tests/ --cov=app.src --cov-report=term-missing

# See which lines aren't tested
# Add test cases for those lines

# Verify coverage improved
pytest app/tests/ --cov=app.src
```

---

## 📈 Step 8: Monitoring & Metrics

### 8.1 Coverage Tracking

**Codecov Integration** (automatic):
1. Tests upload coverage to Codecov
2. View at: `https://codecov.io/gh/baffaabba2/metocean-intelligence`
3. Track trends over time
4. Set coverage goals

**Local Coverage Report**:
```bash
# Generate HTML report
pytest app/tests/ --cov=app.src --cov-report=html

# Open in browser
open htmlcov/index.html
```

### 8.2 Test Speed Metrics

```bash
# Show slowest tests
pytest app/tests/ -v --durations=10

# Typical run times:
# Unit tests:        ~1-2 seconds
# Integration tests: ~3-5 seconds
# Total:             ~10 minutes (including setup)
```

### 8.3 Success Rate Dashboard

```bash
# View success rate
gh run list --workflow tests.yml --status success --limit 20 | wc -l
# ÷ 20 × 100 = success percentage

# View failure rate
gh run list --workflow tests.yml --status failure --limit 20 | wc -l
```

---

## ✅ Completion Checklist

```
GitHub Actions Setup Completed:

☑ Step 1: Secrets Configured
  ☑ SSH_PRIVATE_KEY added
  ☑ VM_IP added
  ☑ VM_USER added
  ☑ (Optional) AWS secrets added

☑ Step 2: Workflows Pushed
  ☑ tests.yml committed
  ☑ code-quality.yml committed
  ☑ deploy-ec2.yml committed
  ☑ All files pushed to main

☑ Step 3: Test Workflow Running
  ☑ First test run passed
  ☑ Coverage check passed
  ☑ All 82 tests passing

☑ Step 4: Deployment Working
  ☑ First deployment successful
  ☑ App running on VM
  ☑ Health endpoint responding

☑ Step 5: Branch Protection Active
  ☑ Status checks required
  ☑ PR reviews enabled
  ☑ Tested on feature branch

☑ Step 6: Monitoring Setup
  ☑ Email notifications enabled
  ☑ GitHub Actions page accessible
  ☑ Codecov integration working

☑ Step 7: Team Trained
  ☑ Developers understand workflow
  ☑ Deployment process documented
  ☑ Troubleshooting guide available
```

---

## 🎓 Next Steps

### This Week
- [ ] Complete all steps above
- [ ] Run first test workflow
- [ ] Run first deployment
- [ ] Share link with team

### This Month
- [ ] Monitor workflow runs
- [ ] Fix any failing tests
- [ ] Reach 85% coverage target
- [ ] Document team procedures

### This Quarter
- [ ] Add performance testing
- [ ] Set up monitoring & alerting
- [ ] Implement blue-green deployments
- [ ] Add canary testing

---

## 📞 Support & Resources

### Get Help

```bash
# View GitHub CLI help
gh help

# View workflow syntax
gh help run

# Debug workflow locally
act  # Requires Docker (local workflow execution)
```

### Documentation

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub CLI Reference](https://cli.github.com/manual/)
- [GitHub Secrets](https://docs.github.com/en/actions/security-guides/using-secrets-in-github-actions)
- [FastAPI Testing](https://fastapi.tiangolo.com/advanced/testing-dependencies/)

### Common Commands

```bash
# List workflows
gh workflow list

# Run workflow
gh workflow run <workflow-name> --ref main

# List runs
gh run list

# View run
gh run view <run-id>

# View logs
gh run view <run-id> --log

# List secrets
gh secret list

# Set secret
gh secret set <name> -b "<value>"
```

---

**Status**: ✅ **Complete**  
**Version**: 2.1.0  
**Last Updated**: 2024-05-26  
**Maintained By**: MetOcean DevOps Team
