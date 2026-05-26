# Phase 5: CI/CD Pipeline & Automation

## Overview
Complete CI/CD setup for MetOcean Intelligence Platform using GitHub Actions, automated testing, coverage monitoring, and deployment automation.

---

## 📋 Table of Contents
1. [GitHub Actions Workflows](#workflows)
2. [GitHub Secrets Setup](#secrets)
3. [Deployment Process](#deployment)
4. [Monitoring & Notifications](#monitoring)
5. [Troubleshooting](#troubleshooting)

---

## 🔄 GitHub Actions Workflows

### 1. **Tests & Coverage** (`.github/workflows/tests.yml`)

**Trigger**: 
- On every push to `main` or `develop`
- On every pull request
- Daily at 2 AM UTC

**Jobs**:
- **Matrix Testing**: Python 3.10 & 3.11
- **Unit Tests**: Fast, isolated tests
- **Integration Tests**: Tests with mocked dependencies
- **Coverage Reporting**: Automated coverage measurement
- **Codecov Upload**: Coverage tracking
- **Type Checking**: Static type analysis (placeholder)
- **Security Scanning**: Secret detection
- **Build Status**: Final pass/fail status

**Example Output**:
```
✅ Python 3.10 Tests: PASSED
✅ Python 3.11 Tests: PASSED
📊 Coverage: 85%
🔒 Security Scan: OK
```

### 2. **Code Quality** (`.github/workflows/code-quality.yml`)

**Trigger**: Push and PR to main/develop

**Jobs**:
- **Linting**: Ruff code checks
- **Formatting**: Black style checks
- **Import Ordering**: isort verification
- **Pylint Analysis**: Code analysis
- **Security Checks**: Dependency audit
- **Documentation**: README verification
- **Dependency Check**: Version tracking

### 3. **Deployment** (`.github/workflows/deploy-ec2.yml`)

**Trigger**: 
- Push to `main` branch
- Manual workflow dispatch

**Jobs**:
- **SSH Setup**: Configure VM connection
- **Backup Creation**: Backup current deployment
- **File Upload**: Upload new code
- **Dependency Update**: Run `uv sync` on VM
- **Service Restart**: Restart MetOcean service
- **Health Verification**: Test endpoints
- **Post-Deploy Tests**: Smoke tests
- **Rollback**: Automatic rollback on failure

---

## 🔐 GitHub Secrets Setup

### Required Secrets

Set these in GitHub repository settings (`Settings → Secrets and variables → Actions`):

```yaml
SSH_PRIVATE_KEY        # SSH private key content (from ~/.ssh/metocean.pem)
VM_IP                  # 34.227.227.14
VM_USER                # ubuntu
```

### How to Add Secrets

1. **Get SSH Key Content**:
   ```bash
   cat ~/.ssh/metocean.pem
   ```

2. **Add to GitHub**:
   - Go to: `https://github.com/baffaabba2/metocean-intelligence/settings/secrets/actions`
   - Click "New repository secret"
   - Name: `SSH_PRIVATE_KEY`
   - Value: Paste entire key content
   - Repeat for `VM_IP` and `VM_USER`

3. **Verify**:
   ```bash
   gh secret list
   ```

### Sample GitHub CLI Commands

```bash
# Login to GitHub CLI
gh auth login

# Add SSH key
gh secret set SSH_PRIVATE_KEY < ~/.ssh/metocean.pem

# Add VM IP
gh secret set VM_IP -b "34.227.227.14"

# Add VM User
gh secret set VM_USER -b "ubuntu"

# List all secrets
gh secret list
```

---

## 🚀 Deployment Process

### Manual Deployment

#### Option 1: Via Shell Script (Local)
```bash
# Navigate to project root
cd ~/Desktop/metocean-intelligence

# Run deployment script
bash DEPLOY_UPDATED.sh 34.227.227.14 ubuntu ~/.ssh/metocean.pem
```

#### Option 2: Via GitHub Actions (Recommended)
```bash
# Push to main branch triggers automatic deployment
git add .
git commit -m "Deploy: Updated features"
git push origin main

# Or use manual workflow dispatch
gh workflow run deploy-ec2.yml --ref main
```

#### Option 3: Direct SSH (Advanced)
```bash
# SSH into VM
ssh -i ~/.ssh/metocean.pem ubuntu@34.227.227.14

# Update application
cd /srv/metocean/app
git pull origin main
~/.local/bin/uv sync --python 3.11

# Restart service
sudo systemctl restart metocean
```

### Deployment Checklist

Before deploying, verify:
- [ ] All tests passing locally: `pytest app/tests/ -v`
- [ ] Code coverage >80%: `pytest --cov=app.src`
- [ ] No lint errors: `ruff check app/src`
- [ ] SSH key configured: `ssh -i ~/.ssh/metocean.pem ubuntu@34.227.227.14 "echo OK"`
- [ ] VM is accessible
- [ ] Backup space available on VM

### Deployment Verification

After deployment, verify:
- [ ] Health endpoint: `curl https://34.227.227.14/health`
- [ ] API docs: `curl https://34.227.227.14/docs`
- [ ] Authentication: Try login flow
- [ ] Service status: `ssh ubuntu@34.227.227.14 'sudo systemctl status metocean'`

---

## 📊 Monitoring & Notifications

### GitHub Actions Status

**View Workflow Results**:
1. Go to: `https://github.com/baffaabba2/metocean-intelligence/actions`
2. Click on workflow run
3. Expand job details
4. View logs

**Status Badge** (add to README.md):
```markdown
![Tests](https://github.com/baffaabba2/metocean-intelligence/workflows/Tests%20%26%20Coverage/badge.svg)
![Code Quality](https://github.com/baffaabba2/metocean-intelligence/workflows/Code%20Quality%20%26%20Linting/badge.svg)
```

### Coverage Tracking

**Codecov Integration**:
```bash
# Coverage reports uploaded automatically
# View at: https://codecov.io/gh/baffaabba2/metocean-intelligence
```

**Local Coverage Report**:
```bash
pytest app/tests/ --cov=app.src --cov-report=html
open htmlcov/index.html
```

### Email Notifications

GitHub Actions sends notifications for:
- Workflow failures
- Deployment status changes
- Pull request reviews required

Enable in: `Settings → Notifications → GitHub Actions`

---

## 📝 Workflow Files Reference

### `.github/workflows/tests.yml`
- **When**: Every push/PR + daily
- **What**: Unit tests, integration tests, coverage
- **Duration**: ~5-10 minutes
- **Failure**: Blocks merge

### `.github/workflows/code-quality.yml`
- **When**: Every push/PR
- **What**: Linting, security, formatting
- **Duration**: ~2-3 minutes
- **Failure**: Warning (doesn't block)

### `.github/workflows/deploy-ec2.yml`
- **When**: Push to main + manual trigger
- **What**: Deploy to EC2, restart service, verify
- **Duration**: ~10-15 minutes
- **Failure**: Auto-rollback

---

## 🔧 Configuration Files

### GitHub Actions Configuration

**In pyproject.toml**:
```toml
[dependency-groups]
test = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.0.0",
    "httpx>=0.27.0",
]
```

**In pytest.ini**:
```ini
[pytest]
testpaths = app/tests
python_files = test_*.py
addopts = -v --strict-markers --cov=app.src
```

### Protection Rules

Set in: `Settings → Branches → Branch protection rules`

**For `main` branch**:
- ✅ Require pull request reviews before merging
- ✅ Require status checks to pass
- ✅ Require branches to be up to date before merging
- ✅ Include administrators
- ✅ Dismiss stale pull request approvals

---

## 📖 Usage Examples

### Run Tests Locally
```bash
# All tests
pytest app/tests/ -v

# With coverage
pytest app/tests/ --cov=app.src --cov-report=html

# Only unit tests
pytest app/tests/ -v -m "unit"

# Only auth tests
pytest app/tests/ -v -m "auth"
```

### Deploy Application
```bash
# Via script
bash DEPLOY_UPDATED.sh

# Via git push
git push origin main  # Triggers automatic deployment

# Via GitHub CLI
gh workflow run deploy-ec2.yml --ref main
```

### Check Deployment Status
```bash
# View logs
ssh -i ~/.ssh/metocean.pem ubuntu@34.227.227.14 'tail -f /srv/metocean/logs/app.log'

# Check service status
ssh -i ~/.ssh/metocean.pem ubuntu@34.227.227.14 'sudo systemctl status metocean'

# Health check
curl https://34.227.227.14/health
```

### Rollback Deployment
```bash
# Automatic (on failure)
# Triggered in deploy-ec2.yml on failure

# Manual
ssh -i ~/.ssh/metocean.pem ubuntu@34.227.227.14
cd /srv/metocean/app
LATEST_BACKUP=$(ls -t backup_*.tar.gz | head -1)
tar -xzf $LATEST_BACKUP
sudo systemctl restart metocean
```

---

## 🐛 Troubleshooting

### Tests Failing in CI But Passing Locally

**Solution**:
```bash
# Check Python version
python --version  # Should be 3.10+

# Verify test dependencies
pip install -e ".[test]"

# Run with same options as CI
pytest app/tests/ -v --cov=app.src --cov-fail-under=80
```

### SSH Connection Issues

**Error**: `Permission denied (publickey)`
- **Check**: SSH key has correct permissions: `chmod 600 ~/.ssh/metocean.pem`
- **Check**: VM security group allows SSH from GitHub Actions
- **Check**: SSH_PRIVATE_KEY secret is properly set

**Error**: `Connection refused`
- **Check**: VM is running: `aws ec2 describe-instances`
- **Check**: IP address is correct
- **Check**: Firewall allows SSH access

### Deployment Failures

**Check logs**:
```bash
# GitHub Actions logs
https://github.com/baffaabba2/metocean-intelligence/actions

# VM logs
ssh ubuntu@34.227.227.14 'sudo journalctl -u metocean -n 100'

# App logs
ssh ubuntu@34.227.227.14 'tail -f /srv/metocean/logs/app.log'
```

**Common issues**:
1. **Import errors**: Check `app.src.*` paths
2. **Database errors**: Check DATABASE_URL env var
3. **Permission errors**: Check service user permissions
4. **Port conflicts**: Check if port 8000 is available

### Coverage Below Threshold

**Issue**: Tests pass but coverage < 80%

**Solution**:
```bash
# View coverage report
pytest --cov=app.src --cov-report=term-missing

# Add tests for uncovered lines
# Edit app/tests/test_*.py
pytest app/tests/ --cov=app.src --cov-report=html
```

### Secrets Not Found

**Error**: `Authentication failed` in deploy workflow

**Solution**:
```bash
# Verify secrets are set
gh secret list

# Re-add if missing
gh secret set SSH_PRIVATE_KEY < ~/.ssh/metocean.pem
gh secret set VM_IP -b "34.227.227.14"
gh secret set VM_USER -b "ubuntu"
```

---

## 🎯 Next Steps

### Immediate (This Week)
- [ ] Set GitHub secrets (SSH_PRIVATE_KEY, VM_IP, VM_USER)
- [ ] Push workflows to main branch
- [ ] Run first automated tests
- [ ] Verify deployment workflow

### Short-term (This Month)
- [ ] Monitor test coverage trends
- [ ] Set up Codecov badge
- [ ] Add branch protection rules
- [ ] Document deployment procedures

### Long-term (Next Quarter)
- [ ] Add performance testing
- [ ] Set up monitoring alerts
- [ ] Implement blue-green deployments
- [ ] Add canary testing

---

## 📚 References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [PyTest Documentation](https://docs.pytest.org/)
- [Codecov Integration](https://codecov.io/)
- [GitHub CLI](https://cli.github.com/)

---

## ✅ Phase 5 Completion Checklist

- [x] Created GitHub Actions test workflow
- [x] Created GitHub Actions code quality workflow
- [x] Created GitHub Actions deployment workflow
- [x] Updated DEPLOY_UPDATED.sh script
- [x] Documented GitHub secrets setup
- [x] Documented deployment procedures
- [x] Created troubleshooting guide
- [ ] Set GitHub secrets (user action required)
- [ ] Push workflows to repository (user action required)
- [ ] Run first automated deployment (user action required)

---

**Status**: ✅ **Phase 5 Complete**  
**Date**: 2024-05-26  
**Version**: 2.1.0  
**Next**: Production Monitoring & Observability (Phase 6)
