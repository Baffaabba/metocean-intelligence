"""
Pytest Configuration for MetOcean Intelligence Platform
Provides shared fixtures for authentication, database, and email testing
"""
import os
import pytest
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient
import tempfile

# Import from app
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def test_db_engine():
    """Create function-scoped in-memory database engine for each test"""
    database_url = "sqlite:///:memory:"
    engine = create_engine(database_url, connect_args={"check_same_thread": False})
    
    # Import models and create all tables for this test
    from app.src.models import Base
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # Cleanup at end of test: drop all tables and dispose engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    
    # Clear all tables from metadata to prevent index conflicts
    # This is critical: removing tables ensures clean state for next test
    for table in list(Base.metadata.tables.values()):
        Base.metadata.remove(table)
    
    # Reset all indexes for clean state
    for constraint in list(Base.metadata.constraints):
        Base.metadata.constraints.discard(constraint)


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
    from app.api import app, get_db
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db_engine)
    
    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    client = TestClient(app)
    yield client
    
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
    from app.src.auth import create_user, create_access_token
    from app.src.db import init_db
    
    # Initialize DB with admin users
    init_db(db_session)
    
    # Get admin token (use first admin email)
    admin_email = "kamaluddeen.usman@utp.edu.my"  # Default admin from db.py
    token = create_access_token(admin_email)
    
    # Set auth header
    test_client.headers = {
        "Authorization": f"Bearer {token}"
    }
    
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
