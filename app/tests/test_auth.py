"""
Authentication Tests for MetOcean Intelligence Platform

Tests all authentication-related functionality:
- User registration (via invitation)
- User login
- JWT token creation and validation
- Password hashing and verification
- Invitation acceptance
- Admin user verification
"""
import pytest
from fastapi import HTTPException
from app.src.auth import (
    hash_password,
    verify_password,
    create_access_token,
    authenticate_user,
    create_invitation,
    accept_invitation,
    get_admin_user,
)


@pytest.mark.auth
@pytest.mark.unit
class TestPasswordHashing:
    """Test password hashing and verification"""
    
    def test_hash_password_creates_different_hash(self):
        """Each password hash should be unique (with salt)"""
        password = "TestPassword123!"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        # Hashes should be different (due to salt)
        assert hash1 != hash2
        # But both should verify
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)
    
    def test_verify_password_succeeds_with_correct_password(self):
        """Correct password should verify"""
        password = "CorrectPassword123!"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed)
    
    def test_verify_password_fails_with_wrong_password(self):
        """Wrong password should not verify"""
        password = "CorrectPassword123!"
        wrong_password = "WrongPassword123!"
        hashed = hash_password(password)
        
        assert not verify_password(wrong_password, hashed)
    
    def test_verify_password_fails_with_empty_password(self):
        """Empty password should not verify"""
        hashed = hash_password("TestPassword123!")
        
        assert not verify_password("", hashed)


@pytest.mark.auth
@pytest.mark.unit
class TestJWTToken:
    """Test JWT token creation and validation"""
    
    def test_create_access_token_returns_string(self):
        """Token creation should return a string"""
        token = create_access_token("user@example.com")
        
        assert isinstance(token, str)
        assert len(token) > 0
        assert "." in token  # JWT format: header.payload.signature
    
    def test_create_access_token_different_emails_different_tokens(self):
        """Different emails should produce different tokens"""
        token1 = create_access_token("user1@example.com")
        token2 = create_access_token("user2@example.com")
        
        assert token1 != token2


@pytest.mark.auth
@pytest.mark.integration
class TestUserAuthentication:
    """Test user authentication flow"""
    
    def test_authenticate_user_with_valid_credentials(self, db_session, test_user_data):
        """Authenticate with valid email and password"""
        from app.src.auth import create_user
        
        # Create user
        user = create_user(db_session, test_user_data["email"], test_user_data["password"])
        
        # Authenticate
        authenticated_user = authenticate_user(db_session, test_user_data["email"], test_user_data["password"])
        
        assert authenticated_user is not None
        assert authenticated_user.email == test_user_data["email"]
    
    def test_authenticate_user_with_wrong_password(self, db_session, test_user_data):
        """Authentication should fail with wrong password"""
        from app.src.auth import create_user
        
        # Create user
        create_user(db_session, test_user_data["email"], test_user_data["password"])
        
        # Try to authenticate with wrong password
        authenticated_user = authenticate_user(db_session, test_user_data["email"], "WrongPassword123!")
        
        assert authenticated_user is None
    
    def test_authenticate_user_with_nonexistent_email(self, db_session):
        """Authentication should return None for non-existent user"""
        authenticated_user = authenticate_user(db_session, "nonexistent@example.com", "SomePassword123!")
        
        assert authenticated_user is None


@pytest.mark.auth
@pytest.mark.integration
class TestInvitationFlow:
    """Test user invitation and acceptance flow"""
    
    def test_create_invitation_creates_invite_record(self, db_session):
        """Creating invitation should add UserInvite to database"""
        email = "newuser@example.com"
        
        invite = create_invitation(db_session, email)
        
        assert invite is not None
        assert invite.email == email
        assert invite.token is not None
        assert len(invite.token) > 0
    
    def test_accept_invitation_creates_user(self, db_session):
        """Accepting invitation should create new user"""
        email = "newuser@example.com"
        password = "NewUserPass123!"
        
        # Create invitation
        invite = create_invitation(db_session, email)
        
        # Accept invitation
        user = accept_invitation(db_session, invite.token, password)
        
        assert user is not None
        assert user.email == email
        assert user.is_active
    
    def test_accept_invitation_with_invalid_token_fails(self, db_session):
        """Accepting with invalid token should raise ValueError"""
        with pytest.raises(ValueError, match="Invitation not found or expired"):
            accept_invitation(db_session, "invalid-token", "Password123!")
    
    def test_accept_invitation_twice_fails(self, db_session):
        """Accepting same invitation twice should fail"""
        email = "newuser@example.com"
        
        # Create and accept invitation
        invite = create_invitation(db_session, email)
        accept_invitation(db_session, invite.token, "Password123!")
        
        # Try to accept same invitation again
        with pytest.raises(ValueError, match="Invitation not found or expired"):
            accept_invitation(db_session, invite.token, "Password123!")


@pytest.mark.auth
@pytest.mark.integration
class TestAdminUsers:
    """Test admin user verification and permissions"""
    
    def test_get_admin_user_with_admin_email(self, db_session):
        """Admin function should accept user with admin email"""
        from app.src.auth import create_user
        from app.src.db import ADMIN_EMAILS
        
        # Create user with admin email
        admin_email = list(ADMIN_EMAILS)[0]
        admin_user = create_user(db_session, admin_email, "AdminPass123!")
        
        # Should not raise exception
        admin_verified = get_admin_user(admin_user)
        assert admin_verified is not None
        assert admin_verified.email == admin_email
    
    def test_get_admin_user_with_non_admin_email_fails(self, db_session):
        """Admin function should reject non-admin user"""
        from app.src.auth import create_user
        
        # Create regular user
        regular_user = create_user(db_session, "regular@example.com", "Pass123!")
        
        # Should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            get_admin_user(regular_user)
        
        assert exc_info.value.status_code == 403


@pytest.mark.auth
@pytest.mark.unit
class TestPasswordReset:
    """Test password reset token generation"""
    
    def test_create_password_reset_token_returns_token(self, db_session):
        """Password reset should create a token"""
        from app.src.auth import create_password_reset_token
        
        email = "user@example.com"
        token = create_password_reset_token(db_session, email)
        
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_password_reset_token_different_for_different_users(self, db_session):
        """Different users should get different reset tokens"""
        from app.src.auth import create_password_reset_token
        
        token1 = create_password_reset_token(db_session, "user1@example.com")
        token2 = create_password_reset_token(db_session, "user2@example.com")
        
        assert token1 != token2


@pytest.mark.auth
class TestAPIAuthenticationFlow:
    """Test authentication through API endpoints"""
    
    def test_login_endpoint_with_valid_credentials(self, test_client, test_user_data, db_session):
        """POST /auth/login with valid credentials should return token"""
        from app.src.auth import create_user
        
        # Create user
        create_user(db_session, test_user_data["email"], test_user_data["password"])
        
        # Login
        response = test_client.post(
            "/auth/login",
            json={
                "email": test_user_data["email"],
                "password": test_user_data["password"],
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_endpoint_with_invalid_credentials(self, test_client):
        """POST /auth/login with invalid credentials should return 401"""
        response = test_client.post(
            "/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "WrongPassword123!",
            }
        )
        
        assert response.status_code == 401
    
    def test_verify_token_endpoint_with_valid_token(self, authenticated_client):
        """GET /auth/verify with valid token should return 200"""
        response = authenticated_client.get("/auth/verify")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
    
    def test_verify_token_endpoint_without_token(self, test_client):
        """GET /auth/verify without token should return 401"""
        response = test_client.get("/auth/verify")
        
        assert response.status_code == 401
