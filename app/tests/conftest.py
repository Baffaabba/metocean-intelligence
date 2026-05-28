"""
Pytest Configuration for MetOcean Intelligence Platform
Provides shared fixtures for authentication, database, and email testing
"""
import os
import pytest
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

# Import from app
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ---------------------------------------------------------------------------
# CRITICAL: Prevent duplicate module execution caused by mixed import paths.
#
# Source files in app/src/ use:  "from src.xxx import yyy"   (via app/ in path)
# api.py uses:                   "from app.src.xxx import yyy" (from repo root)
#
# When Python sees both paths pointing to the same .py file, it executes
# models.py TWICE — once as "src.models" and once as "app.src.models".
# The second execution runs "class User(Base)" again with extend_existing=True,
# which APPENDS duplicate Index objects to Base.metadata.  When create_all()
# runs it then issues CREATE INDEX twice on the same empty database, which
# SQLite rejects with "index already exists".
#
# Fix: after loading the src.* modules the normal way, alias them under the
# app.src.* names so Python returns the cached objects instead of re-running
# the module file.
# ---------------------------------------------------------------------------
import src.db       # noqa: F401 – populates sys.modules['src.db']
import src.models   # noqa: F401 – populates sys.modules['src.models']
import src.auth     # noqa: F401 – populates sys.modules['src.auth']

sys.modules.setdefault('app.src.db',     sys.modules['src.db'])
sys.modules.setdefault('app.src.models', sys.modules['src.models'])
sys.modules.setdefault('app.src.auth',   sys.modules['src.auth'])


@pytest.fixture
def test_db_engine():
    """Create function-scoped in-memory SQLite database for each test.

    Module aliasing at the top of this file ensures models.py is executed
    only once, so Base.metadata contains exactly one Index object per index
    (no duplicates).  Each call to this fixture creates a fresh :memory:
    engine, so tables/indexes are always created on a completely empty DB.
    """
    from src.db import Base

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(bind=engine)

    yield engine

    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def temp_db(test_db_engine):
    """Create fresh session for each test"""
    from sqlalchemy.orm import sessionmaker
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db_engine)
    session = SessionLocal()
    
    yield session
    
    # Cleanup session
    session.close()


@pytest.fixture
def db_session(temp_db):
    """Get database session for tests"""
    return temp_db


@pytest.fixture
def test_user_data():
    """Sample user data for testing"""
    return {
        "email": "test@example.com",
        "password": "SecurePass123!",
    }


@pytest.fixture
def test_admin_data():
    """Sample admin user data"""
    return {
        "email": "admin@example.com",
        "password": "AdminPass123!",
    }


@pytest.fixture
def mock_env(monkeypatch):
    """Mock environment variables for testing"""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///test.db")
    monkeypatch.setenv("METOCEAN_JWT_SECRET_KEY", "test-secret-key-for-testing-only")
    monkeypatch.setenv("METOCEAN_JWT_EXPIRE_MINUTES", "60")
    # Mock AWS SES (optional - will skip if not configured)
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test-key")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test-secret")
    monkeypatch.setenv("SENDER_EMAIL", "test@example.com")


@pytest.fixture
def test_client(mock_env, test_db_engine):
    """Create TestClient for API testing"""
    import app.api as api_module
    from app.api import app, get_db
    from src.db import Base

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db_engine)

    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    # init_db() uses the module-level postgres engine which is unavailable in CI.
    # Replace it with a no-op so the lifespan doesn't blow up during tests.
    # Tables are already created by test_db_engine; get_db is overridden above.
    original_init_db = api_module.init_db
    api_module.init_db = lambda: None

    app.dependency_overrides[get_db] = override_get_db

    client = TestClient(app)
    yield client

    api_module.init_db = original_init_db
    app.dependency_overrides.clear()


@pytest.fixture
def authenticated_client(test_client, test_user_data, db_session):
    """Client with authentication token"""
    # First register/create user
    from app.src.auth import create_user, create_access_token
    from app.src.db import get_db
    
    # Create user
    user = create_user(db_session, test_user_data["email"], test_user_data["password"])
    
    # Get token
    token = create_access_token(test_user_data["email"])
    
    # Set auth header
    test_client.headers = {
        "Authorization": f"Bearer {token}"
    }
    
    return test_client


@pytest.fixture
def admin_client(test_client, test_admin_data, db_session):
    """Client with admin authentication token"""
    from app.src.auth import create_access_token, hash_password
    from app.src.models import User

    # The JWT token and the DB user MUST use the same email.
    # Use a hardcoded admin email (in ADMIN_EMAILS) so the endpoint
    # recognises this user as admin even without is_admin=True in the DB.
    admin_email = "kamaluddeen.usman@utp.edu.my"

    try:
        admin = User(
            email=admin_email,
            hashed_password=hash_password(test_admin_data["password"]),
            is_admin=True,
        )
        db_session.add(admin)
        db_session.commit()
    except Exception:
        db_session.rollback()  # user may already exist

    token = create_access_token(admin_email)
    test_client.headers = {"Authorization": f"Bearer {token}"}
    
    return test_client


# Pytest configuration
def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "auth: mark test as related to authentication")
    config.addinivalue_line("markers", "email: mark test as related to email service")
    config.addinivalue_line("markers", "api: mark test as related to API endpoints")
    config.addinivalue_line("markers", "forecast: mark test as related to forecasting")


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
