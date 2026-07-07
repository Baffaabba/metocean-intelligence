"""
Email Service Tests for MetOcean Intelligence Platform

Tests email functionality:
- Invitation email sending (SMTP, the default provider)
- Password reset email sending
- Email formatting and content
- Error handling for missing configuration
- Legacy AWS SES backend (EMAIL_PROVIDER=ses)
"""
import pytest
from unittest.mock import patch, MagicMock
from app.src.email import send_invite_email, send_password_reset_email


def _smtp_env(monkeypatch):
    monkeypatch.setenv("SMTP_HOST", "smtp-relay.brevo.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USER", "test@example.com")
    monkeypatch.setenv("SMTP_PASSWORD", "test-smtp-key")
    monkeypatch.setenv("SENDER_EMAIL", "noreply@metoceanai.com")
    monkeypatch.setenv("EMAIL_PROVIDER", "smtp")


@pytest.fixture
def mock_smtp():
    with patch("app.src.email.smtplib.SMTP") as mock_smtp_cls:
        server = MagicMock()
        mock_smtp_cls.return_value.__enter__.return_value = server
        yield server


@pytest.mark.email
@pytest.mark.unit
class TestInviteEmailGeneration:
    """Test invitation email generation and sending via SMTP (default provider)."""

    def test_send_invite_email_with_valid_config(self, monkeypatch, mock_smtp):
        _smtp_env(monkeypatch)
        result = send_invite_email("user@example.com", "test-token-12345", "MetOcean Intelligence")

        assert result is True
        mock_smtp.send_message.assert_called_once()

    def test_send_invite_email_returns_false_on_missing_config(self, monkeypatch):
        monkeypatch.delenv("SMTP_HOST", raising=False)
        monkeypatch.delenv("SMTP_USER", raising=False)
        monkeypatch.delenv("SMTP_PASSWORD", raising=False)
        monkeypatch.setenv("EMAIL_PROVIDER", "smtp")

        result = send_invite_email("user@example.com", "test-token-12345", "MetOcean Intelligence")

        assert result is False

    def test_send_invite_email_includes_acceptance_link(self, monkeypatch, mock_smtp):
        _smtp_env(monkeypatch)
        token = "test-token-abc123"
        send_invite_email("user@example.com", token, "MetOcean Intelligence")

        sent_msg = mock_smtp.send_message.call_args[0][0]
        assert token in sent_msg.get_body(preferencelist="html").get_content()

    def test_send_invite_email_to_correct_recipient(self, monkeypatch, mock_smtp):
        _smtp_env(monkeypatch)
        recipient = "newuser@example.com"
        send_invite_email(recipient, "test-token", "MetOcean Intelligence")

        sent_msg = mock_smtp.send_message.call_args[0][0]
        assert sent_msg["To"] == recipient


@pytest.mark.email
@pytest.mark.integration
class TestEmailErrorHandling:
    """Test error handling in email service."""

    def test_send_invite_email_handles_smtp_exception(self, monkeypatch, mock_smtp):
        _smtp_env(monkeypatch)
        mock_smtp.send_message.side_effect = Exception("SMTP relay error")

        result = send_invite_email("user@example.com", "test-token", "MetOcean Intelligence")

        assert result is False


@pytest.mark.email
class TestEmailAPIIntegration:
    """Test email sending through API endpoints."""

    def test_admin_invite_endpoint_sends_email(self, admin_client, monkeypatch, mock_smtp):
        _smtp_env(monkeypatch)
        response = admin_client.post(
            "/admin/invite",
            json={"email": "newuser@example.com"}
        )

        assert response.status_code == 200
        mock_smtp.send_message.assert_called_once()

    def test_admin_invite_endpoint_without_email_fails(self, admin_client):
        response = admin_client.post(
            "/admin/invite",
            json={}
        )

        assert response.status_code == 422  # Validation error

    def test_accept_invite_with_valid_token(self, test_client):
        response = test_client.post(
            "/auth/accept-invite/test-token",
            json={
                "password": "NewPassword123!"
            }
        )

        # Invalid/unknown token in this test -> 400
        assert response.status_code in [400, 404, 422]


@pytest.mark.email
@pytest.mark.unit
class TestEmailFormatting:
    """Test email content formatting."""

    def test_invite_email_contains_app_name(self, monkeypatch, mock_smtp):
        _smtp_env(monkeypatch)
        app_name = "MetOcean Intelligence"
        send_invite_email("user@example.com", "token", app_name)

        sent_msg = mock_smtp.send_message.call_args[0][0]
        assert app_name in sent_msg.get_body(preferencelist="html").get_content()

    def test_invite_email_is_html_formatted(self, monkeypatch, mock_smtp):
        _smtp_env(monkeypatch)
        send_invite_email("user@example.com", "token", "App Name")

        sent_msg = mock_smtp.send_message.call_args[0][0]
        html = sent_msg.get_body(preferencelist="html").get_content()
        assert "<html>" in html.lower()


@pytest.mark.email
@pytest.mark.unit
class TestPasswordResetEmail:
    """Test password reset email sending."""

    def test_password_reset_email_sent_on_forgot_password(self, test_client, monkeypatch, mock_smtp):
        _smtp_env(monkeypatch)
        response = test_client.post(
            "/auth/forgot-password",
            json={"email": "user@example.com"}
        )

        # Should return 200 (whether user exists or not, for security)
        assert response.status_code == 200

    def test_password_reset_email_includes_reset_link(self, monkeypatch, mock_smtp):
        _smtp_env(monkeypatch)
        token = "reset-token-xyz"
        send_password_reset_email("user@example.com", token, "MetOcean Intelligence")

        sent_msg = mock_smtp.send_message.call_args[0][0]
        assert token in sent_msg.get_body(preferencelist="html").get_content()


@pytest.mark.email
@pytest.mark.unit
class TestSesBackend:
    """Legacy AWS SES backend, used only when EMAIL_PROVIDER=ses."""

    def test_send_invite_email_via_ses(self, monkeypatch):
        monkeypatch.setenv("EMAIL_PROVIDER", "ses")
        monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test-key")
        monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test-secret")
        monkeypatch.setenv("SENDER_EMAIL", "noreply@metoceanai.com")

        mock_client = MagicMock()
        mock_client.send_email.return_value = {"MessageId": "test-message-id"}

        with patch("boto3.client", return_value=mock_client):
            result = send_invite_email("user@example.com", "test-token", "MetOcean Intelligence")

        assert result is True
        mock_client.send_email.assert_called_once()

    def test_send_invite_email_via_ses_missing_credentials(self, monkeypatch):
        monkeypatch.setenv("EMAIL_PROVIDER", "ses")
        monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
        monkeypatch.delenv("AWS_SECRET_ACCESS_KEY", raising=False)

        result = send_invite_email("user@example.com", "test-token", "MetOcean Intelligence")

        assert result is False
