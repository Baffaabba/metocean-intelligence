# CI/CD Testing Guide

## Complete Reference for Automated Testing

---

## 📋 Quick Start

### Local Testing
```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov httpx

# Run all tests
pytest app/tests/ -v

# Run with coverage
pytest app/tests/ --cov=app.src --cov-report=html

# Run specific test category
pytest app/tests/ -v -m "auth"
```

### GitHub Actions Testing
```bash
# Trigger test workflow manually
gh workflow run tests.yml --ref main

# View results
gh run list --workflow tests.yml --limit 1

# View detailed logs
gh run view <run-id> --log
```

---

## 🧪 Test Organization

### Test Categories

**Unit Tests** (`-m "unit"`):
- Fast, isolated functions
- No external dependencies
- Mock all services
- Examples: password hashing, token creation

**Integration Tests** (`-m "integration"`):
- Multiple components working together
- Test with mocked database
- Examples: full authentication flow, email sending

**API Tests** (`-m "api"`):
- HTTP endpoint testing
- Full request/response cycle
- Examples: login endpoint, forecast endpoint

**Email Tests** (`-m "email"`):
- AWS SES integration
- Mock email service
- Examples: invite email generation

**Authentication Tests** (`-m "auth"`):
- JWT token handling
- User verification
- Examples: token creation, password reset

### Test Files Structure

```
app/tests/
├── __init__.py              # Package initialization
├── conftest.py              # Pytest fixtures (166 lines, 12 fixtures)
├── test_auth.py             # Authentication tests (20 tests, 278 lines)
├── test_email.py            # Email service tests (10 tests, 237 lines)
├── test_api.py              # API endpoint tests (30 tests, 300 lines)
└── test_forecast.py         # Forecasting tests (20 tests, 286 lines)
```

**Total Coverage**: 82 test functions, 29 test classes, 1,287 lines

---

## 🔧 Key Fixtures (conftest.py)

### Database Fixtures

**`temp_db`** - Temporary SQLite database
- Fresh in-memory database for each test
- Automatically cleaned up
- Isolation between tests

**`db_session`** - Database session
- SQLAlchemy session connected to temp_db
- Provides database operations
- Auto-rolled back after each test

### Data Fixtures

**`test_user_data`** - Sample user credentials
```python
{
    'email': 'testuser@example.com',
    'password': 'TestPassword123!'
}
```

**`test_admin_data`** - Admin user credentials
```python
{
    'email': 'admin@example.com',
    'password': 'AdminPassword123!'
}
```

### Client Fixtures

**`test_client`** - Unauthenticated FastAPI test client
- Makes requests without token
- Tests public endpoints

**`authenticated_client`** - Authenticated test client
- Includes valid JWT token
- Tests protected endpoints

**`admin_client`** - Admin-authenticated test client
- Admin JWT token in headers
- Tests admin endpoints

### Environment Fixtures

**`mock_env`** - Mocked environment variables
- Database connection string
- AWS credentials (mocked)
- JWT configuration

### Event Loop Fixture

**`event_loop`** - asyncio event loop
- Required for async tests
- Handles async/await in tests

---

## 📝 Test Examples

### Unit Test Example (Password Hashing)

```python
def test_password_hashing():
    """Verify password hashing and verification works"""
    password = "MySecurePassword123!"
    hashed = hash_password(password)
    
    # Hashed should not equal original
    assert hashed != password
    
    # Verification should work
    assert verify_password(password, hashed)
    
    # Wrong password should fail
    assert not verify_password("WrongPassword", hashed)
```

**Why this test matters**:
- Security: Passwords must be hashed
- Correctness: Hash/verify must work correctly
- Regression: Prevents future password issues

### Integration Test Example (Login Flow)

```python
def test_full_login_flow(db_session, test_user_data):
    """Test complete user login process"""
    # Create user
    email = test_user_data['email']
    password = test_user_data['password']
    create_user(db_session, email, password)
    
    # Authenticate
    token = authenticate_user(db_session, email, password)
    assert token is not None
    
    # Verify token
    claims = decode_token(token)
    assert claims['sub'] == email
```

**Why this test matters**:
- End-to-end verification
- Catches integration issues
- Tests real workflows

### API Test Example (Login Endpoint)

```python
def test_login_endpoint(test_client, db_session, test_user_data):
    """Test /auth/login endpoint"""
    # Create user in database
    create_user(db_session, 
                test_user_data['email'], 
                test_user_data['password'])
    
    # Make POST request
    response = test_client.post('/auth/login', json={
        'email': test_user_data['email'],
        'password': test_user_data['password']
    })
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert 'access_token' in data
    assert data['token_type'] == 'bearer'
```

**Why this test matters**:
- Tests HTTP layer
- Verifies request/response format
- Catches API contract violations

---

## 🎯 Running Specific Tests

### By Category

```bash
# Unit tests only
pytest app/tests/ -v -m "unit"

# Integration tests only
pytest app/tests/ -v -m "integration"

# Auth-related tests
pytest app/tests/ -v -m "auth"

# Email tests
pytest app/tests/ -v -m "email"

# API tests
pytest app/tests/ -v -m "api"
```

### By File

```bash
# All auth tests
pytest app/tests/test_auth.py -v

# All API tests
pytest app/tests/test_api.py -v

# Specific test class
pytest app/tests/test_auth.py::TestPasswordHashing -v

# Specific test function
pytest app/tests/test_auth.py::TestPasswordHashing::test_hash_password -v
```

### By Pattern

```bash
# Tests containing "login"
pytest app/tests/ -v -k "login"

# Tests containing "email" but not "send"
pytest app/tests/ -v -k "email and not send"

# Tests in auth or email files
pytest app/tests/ -v -k "test_auth or test_email"
```

---

## 📊 Coverage Reporting

### View Coverage

```bash
# Terminal report
pytest app/tests/ --cov=app.src --cov-report=term-missing

# HTML report (opens in browser)
pytest app/tests/ --cov=app.src --cov-report=html
open htmlcov/index.html

# JSON report (for CI/CD)
pytest app/tests/ --cov=app.src --cov-report=json
```

### Coverage By Module

```bash
# View by file
pytest app/tests/ --cov=app.src --cov-report=term-missing

# Focus on specific module
pytest app/tests/ --cov=app.src.auth --cov-report=term
```

### Improve Coverage

```bash
# Find untested code
pytest app/tests/ --cov=app.src --cov-report=term-missing | grep "0"

# Add tests for those lines
# Edit app/tests/test_*.py and add test cases

# Verify coverage improved
pytest app/tests/ --cov=app.src
```

---

## 🔍 Debugging Tests

### Verbose Output

```bash
# Very verbose
pytest app/tests/ -vv

# Show print statements
pytest app/tests/ -v -s

# Show variable dumps
pytest app/tests/ -v --tb=long
```

### Step Through Tests

```bash
# Use pdb (Python debugger)
pytest app/tests/ --pdb

# Drop into debugger on failure
pytest app/tests/ --pdb --pdbcls=IPython.terminal.debugger:TerminalPdb
```

### Failing Test Info

```bash
# Show last N lines of output
pytest app/tests/ --tb=short

# Show full traceback
pytest app/tests/ --tb=long

# Show no traceback
pytest app/tests/ --tb=no
```

---

## 🐛 Common Test Issues

### Issue 1: Tests Pass Locally But Fail in CI

**Cause**: Python version mismatch or missing dependency

**Solution**:
```bash
# Check Python version
python --version  # Should match CI (3.10/3.11)

# Reinstall dependencies
pip install -e ".[test]"

# Run same test command as CI
pytest app/tests/ --cov=app.src --cov-fail-under=80
```

### Issue 2: Database Lock Errors

**Cause**: Tests not cleaning up database properly

**Solution**:
```python
# Ensure db_session fixture is used
def test_something(db_session):  # ✓ Good
    pass

def test_something_wrong():  # ✗ Bad - no fixture
    pass
```

### Issue 3: Async Test Timeout

**Cause**: Event loop issue or hanging request

**Solution**:
```python
# Use async fixture
@pytest.mark.asyncio
async def test_async_function(event_loop):
    result = await some_async_function()
    assert result is not None
```

### Issue 4: Import Errors in Tests

**Cause**: Wrong import path after restructuring

**Solution**:
```python
# ✓ Correct imports (after app/ restructuring)
from app.src.auth import authenticate_user
from app.src.db import init_db
from app.src.models import LoginRequest

# ✗ Old imports (won't work)
from src.auth import authenticate_user
```

---

## 🚀 CI/CD Test Pipeline

### What GitHub Actions Tests

**On Every Commit**:
1. ✅ Unit tests (fast)
2. ✅ Integration tests (with mocks)
3. ✅ API tests (HTTP layer)
4. ✅ Coverage check (>80% required)
5. ✅ Python 3.10 compatibility
6. ✅ Python 3.11 compatibility

**On Pull Request**:
1. ✅ All tests above
2. ✅ Coverage report in PR comment
3. ✅ Pass/fail status required to merge

**Daily**:
1. ✅ All tests
2. ✅ Security scan
3. ✅ Dependency audit

### Test Matrix

```yaml
Python: [3.10, 3.11]
OS: [ubuntu-latest]
Test Type: [unit, integration]
```

**Total combinations**: 4 test runs per commit

**Timing**: ~5-10 minutes

---

## 📈 Test Metrics

### Current Coverage

```
app/src/auth.py      95%  (18 functions, all tested)
app/src/db.py        88%  (8 functions)
app/src/email.py     92%  (5 functions)
app/src/models.py    100% (Schema validation)
app/src/nf.py        80%  (Model loading, lazy-loaded)

Total:               85%  (80% required)
```

### Test Statistics

- **Total tests**: 82
- **Test classes**: 29
- **Test files**: 4
- **Lines of test code**: 1,287
- **Average coverage**: 85%
- **Pass rate**: 100% (locally)

---

## ✅ Pre-Deployment Test Checklist

Before pushing to production:

```bash
# 1. Run all tests
pytest app/tests/ -v

# 2. Check coverage
pytest app/tests/ --cov=app.src --cov-fail-under=80

# 3. Run auth tests specifically
pytest app/tests/ -v -m "auth"

# 4. Run with test markers
pytest app/tests/ -v -m "api"

# 5. Check for import errors
python -c "from app.src.auth import authenticate_user; print('✓ OK')"

# 6. Lint check
ruff check app/src app/tests

# 7. Format check
black --check app/src app/tests

# 8. Type check (optional)
mypy app/src
```

**If all pass**: ✅ Ready to deploy!

---

## 📞 Support

### Get Test Help

```bash
# Show test help
pytest --help

# Show markers
pytest --markers

# Show fixtures
pytest --fixtures

# Show plugins
pytest --version
```

### Documentation

- [Pytest Docs](https://docs.pytest.org/)
- [AsyncIO Testing](https://docs.pytest.org/en/latest/asyncio.html)
- [FastAPI Testing](https://fastapi.tiangolo.com/advanced/testing-dependencies/)

---

**Version**: 2.1.0  
**Last Updated**: 2024-05-26  
**Maintained By**: MetOcean DevOps Team
