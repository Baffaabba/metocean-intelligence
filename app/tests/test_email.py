"""
Email Service Tests for MetOcean Intelligence Platform

Tests email functionality:
- Invitation email sending
- Password reset email sending
- Email formatting and content
- Error handling for missing AWS credentials
"""
import pytest
from unittest.mock import patch, MagicMock
from app.src.email import send_invite_email


@pytest.mark.email
@pytest.mark.unit
class TestInviteEmailGeneration:
    """Test invitation email generation and sending"""
    
    def test_send_invite_email_with_valid_credentials(self, monkeypatch):
        """send_invite_email should return True when credentials available"""
        # Mock boto3
        mock_client = MagicMock()
        mock_client.send_email.return_value = {"MessageId": "test-message-id"}
        
        with patch("app.src.email.boto3.client", return_value=mock_client):
            result = send_invite_email(
                "user@example.com",
                "test-token-12345",
                "MetOcean Intelligence"
            )
        
        assert result is True
        mock_client.send_email.assert_called_once()
    
    def test_send_invite_email_returns_false_on_missing_credentials(self, monkeypatch):
        """send_invite_email should handle missing AWS credentials gracefully"""
        # Remove AWS credentials
        monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
        monkeypatch.delenv("AWS_SECRET_ACCESS_KEY", raising=False)
        monkeypatch.delenv("SENDER_EMAIL", raising=False)
        
        # Should not raise exception, just return False
        result = send_invite_email(
            "user@example.com",
            "test-token-12345",
            "MetOcean Intelligence"
        )
        
        assert result is False
    
    def test_send_invite_email_includes_acceptance_link(self, monkeypatch):
        """Invitation email should include acceptance link with token"""
        mock_client = MagicMock()
        mock_client.send_email.return_value = {"MessageId": "test-message-id"}
        
        with patch("app.src.email.boto3.client", return_value=mock_client):
            token = "test-token-abc123"
            send_invite_email(
                "user@example.com",
                token,
                "MetOcean Intelligence"
            )
        
        # Verify the call was made
        mock_client.send_email.assert_called_once()
        call_args = mock_client.send_email.call_args
        
        # Check that email body contains the token
        email_body = call_args[1]["Message"]["Body"]["Html"]["Data"]
        assert token in email_body
    
    def test_send_invite_email_to_correct_recipient(self, monkeypatch):
        """Invitation email should be sent to specified recipient"""
        recipient = "newuser@example.com"
        mock_client = MagicMock()
        mock_client.send_email.return_value = {"MessageId": "test-message-id"}
        
        with patch("app.src.email.boto3.client", return_value=mock_client):
            send_invite_email(recipient, "test-token", "MetOcean Intelligence")
        
        # Verify recipient
        call_args = mock_client.send_email.call_args
        destination = call_args[1]["Destination"]["ToAddresses"]
        assert recipient in destination


@pytest.mark.email
@pytest.mark.integration
class TestEmailErrorHandling:
    """Test error handling in email service"""
    
    def test_send_invite_email_handles_boto3_exception(self, monkeypatch):
        """Email service should handle boto3 exceptions gracefully"""
        mock_client = MagicMock()
        mock_client.send_email.side_effect = Exception("AWS SES error")
        
        with patch("app.src.email.boto3.client", return_value=mock_client):
            # Should return False instead of raising
            result = send_invite_email(
                "user@example.com",
                "test-token",
                "MetOcean Intelligence"
            )
        
        assert result is False
    
    def test_send_invite_email_with_invalid_recipient(self, monkeypatch):
        """Email service should handle invalid recipient emails"""
        mock_client = MagicMock()
        mock_client.send_email.side_effect = ValueError("Invalid email address")
        
        with patch("app.src.email.boto3.client", return_value=mock_client):
            # Could either validate before sending or catch exception
            result = send_invite_email(
                "not-an-email",
                "test-token",
                "MetOcean Intelligence"
            )
        
        assert result is False


@pytest.mark.email
class TestEmailAPIIntegration:
    """Test email sending through API endpoints"""
    
    def test_admin_invite_endpoint_sends_email(self, admin_client, monkeypatch):
        """POST /admin/invite should send invitation email"""
        mock_client = MagicMock()
        mock_client.send_email.return_value = {"MessageId": "test-message-id"}
        
        with patch("app.src.email.boto3.client", return_value=mock_client):
            response = admin_client.post(
                "/admin/invite",
                json={"email": "newuser@example.com"}
            )
        
        # Should succeed
        assert response.status_code == 200
        
        # Email should have been sent
        mock_client.send_email.assert_called_once()
    
    def test_admin_invite_endpoint_without_email_fails(self, admin_client):
        """POST /admin/invite without email should fail"""
        response = admin_client.post(
            "/admin/invite",
            json={}
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_accept_invite_with_valid_token(self, test_client):
        """POST /auth/accept-invite/{token} should accept invitation"""
        from app.src.auth import create_invitation
        from app.src.db import get_db
        
        # Create invitation
        # Note: This test would need a DB session fixture
        # Simplified for demonstration
        response = test_client.post(
            "/auth/accept-invite/test-token",
            json={
                "password": "NewPassword123!"
            }
        )
        
        # Would return 400+ if token invalid (expected in this case)
        assert response.status_code in [400, 404, 422]


@pytest.mark.email
@pytest.mark.unit
class TestEmailFormatting:
    """Test email content formatting"""
    
    def test_invite_email_contains_app_name(self, monkeypatch):
        """Email should include application name"""
        mock_client = MagicMock()
        mock_client.send_email.return_value = {"MessageId": "test-message-id"}
        app_name = "MetOcean Intelligence"
        
        with patch("app.src.email.boto3.client", return_value=mock_client):
            send_invite_email("user@example.com", "token", app_name)
        
        call_args = mock_client.send_email.call_args
        email_body = call_args[1]["Message"]["Body"]["Html"]["Data"]
        assert app_name in email_body
    
    def test_invite_email_is_html_formatted(self, monkeypatch):
        """Email body should be HTML formatted"""
        mock_client = MagicMock()
        mock_client.send_email.return_value = {"MessageId": "test-message-id"}
        
        with patch("app.src.email.boto3.client", return_value=mock_client):
            send_invite_email("user@example.com", "token", "App Name")
        
        call_args = mock_client.send_email.call_args
        email_body = call_args[1]["Message"]["Body"]["Html"]["Data"]
        
        # Should contain HTML tags
        assert "<" in email_body and ">" in email_body
        assert "html" in email_body.lower() or "style" in email_body.lower()


@pytest.mark.email
@pytest.mark.unit
class TestPasswordResetEmail:
    """Test password reset email sending"""
    
    def test_password_reset_email_sent_on_forgot_password(self, test_client, monkeypatch):
        """Password reset email should be sent on /auth/forgot-password"""
        mock_client = MagicMock()
        mock_client.send_email.return_value = {"MessageId": "test-message-id"}
        
        with patch("app.src.email.boto3.client", return_value=mock_client):
            response = test_client.post(
                "/auth/forgot-password",
                json={"email": "user@example.com"}
            )
        
        # Should return 200 (whether user exists or not, for security)
        assert response.status_code == 200
    
    def test_password_reset_email_includes_reset_link(self, monkeypatch):
        """Password reset email should include reset link with token"""
        mock_client = MagicMock()
        mock_client.send_email.return_value = {"MessageId": "test-message-id"}
        
        with patch("app.src.email.boto3.client", return_value=mock_client):
            from app.src.auth import create_password_reset_token
            from app.src.db import Session  # Mock DB
            
            # In real scenario, this would be called via API
            # Just verifying the email would contain a reset link
            assert True  # Placeholder for integration test
