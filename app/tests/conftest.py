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

# auth.py now refuses to import without METOCEAN_JWT_SECRET set (no more
# insecure "change-this-in-production" fallback). Set it here, before any
# app.src.* import below, so test collection doesn't blow up.
os.environ.setdefault("METOCEAN_JWT_SECRET", "test-secret-key-for-testing-only-not-for-prod")

# All internal app/src/*.py modules import each other via "app.src.x", the
# same style api.py itself uses — so this is the only import path that ever
# gets exercised, matching exactly how uvicorn app.api:app runs in
# production. pytest.ini's `pythonpath = .` puts the repo root on sys.path.


@pytest.fixture
def test_db_engine():
    """Create function-scoped in-memory SQLite database for each test."""
    from app.src.db import Base

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
    monkeypatch.setenv("METOCEAN_JWT_SECRET", "test-secret-key-for-testing-only-not-for-prod")
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

    # Rate limiting is per-process/in-memory and keyed by client IP; reset it
    # so earlier tests hitting /auth/login etc. don't trip the limit here.
    if hasattr(api_module.limiter, "reset"):
        api_module.limiter.reset()

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
