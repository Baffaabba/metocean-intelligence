"""
Email service for sending invitations and password-reset notifications.

Supports two backends, selected via EMAIL_PROVIDER:
  - "smtp" (default): any SMTP relay — Brevo's free tier, Gmail with an App
    Password, etc. Uses stdlib smtplib, no extra dependency.
  - "ses": AWS SES via boto3 (legacy path, kept for accounts that already
    have SES production access).
"""

import logging
import os
import smtplib
from email.message import EmailMessage
from typing import Optional

logger = logging.getLogger("metocean.email")


def _build_invite_email(app_name: str, accept_url: str) -> tuple[str, str, str]:
    subject = f"Invitation to {app_name}"
    html_body = f"""
    <html>
        <head></head>
        <body>
            <h2>Welcome to {app_name}!</h2>
            <p>You have been invited to join {app_name}.</p>
            <p>
                <a href="{accept_url}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">
                    Accept Invitation & Set Password
                </a>
            </p>
            <p>Or copy this link:</p>
            <p><code>{accept_url}</code></p>
            <p>This invitation link will expire in 7 days.</p>
            <br>
            <p>Regards,<br>The {app_name} Team</p>
        </body>
    </html>
    """
    text_body = f"""
    Welcome to {app_name}!

    You have been invited to join {app_name}.

    Click the link below to accept the invitation and set your password:
    {accept_url}

    This invitation link will expire in 7 days.

    Regards,
    The {app_name} Team
    """
    return subject, text_body, html_body


def _build_reset_email(app_name: str, reset_url: str) -> tuple[str, str, str]:
    subject = f"Password Reset - {app_name}"
    html_body = f"""
    <html>
        <head></head>
        <body>
            <h2>Password Reset Request</h2>
            <p>We received a request to reset your password.</p>
            <p>
                <a href="{reset_url}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">
                    Reset Password
                </a>
            </p>
            <p>This link will expire in 1 hour.</p>
            <br>
            <p>Regards,<br>The {app_name} Team</p>
        </body>
    </html>
    """
    text_body = f"""
    Password Reset Request

    We received a request to reset your password. This link expires in 1 hour:
    {reset_url}

    Regards,
    The {app_name} Team
    """
    return subject, text_body, html_body


def _send_via_smtp(recipient_email: str, subject: str, text_body: str, html_body: str) -> bool:
    smtp_host = os.getenv("SMTP_HOST", "")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_password = os.getenv("SMTP_PASSWORD", "")
    sender_email = os.getenv("SENDER_EMAIL", smtp_user)

    if not smtp_host or not smtp_user or not smtp_password:
        logger.error("Cannot send email: SMTP_HOST/SMTP_USER/SMTP_PASSWORD not configured")
        return False

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype="html")

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        logger.info(f"Email sent to {recipient_email} via SMTP ({smtp_host}).")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {recipient_email} via SMTP: {e}")
        return False


def _send_via_ses(recipient_email: str, subject: str, text_body: str, html_body: str) -> bool:
    try:
        import boto3
        from botocore.exceptions import ClientError
    except ImportError:
        logger.error("EMAIL_PROVIDER=ses but boto3 is not installed.")
        return False

    aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID", "")
    aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    if not aws_access_key_id or not aws_secret_access_key:
        logger.error("Cannot send email: AWS SES credentials not configured")
        return False

    sender_email = os.getenv("SENDER_EMAIL", "noreply@metoceanai.com")
    client = boto3.client(
        "ses",
        region_name=os.getenv("AWS_REGION", "us-east-1"),
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
    )
    try:
        response = client.send_email(
            Source=sender_email,
            Destination={"ToAddresses": [recipient_email]},
            Message={
                "Subject": {"Data": subject},
                "Body": {
                    "Text": {"Data": text_body},
                    "Html": {"Data": html_body},
                },
            },
        )
        logger.info(f"Email sent to {recipient_email} via SES. MessageId: {response['MessageId']}")
        return True
    except ClientError as e:
        logger.error(f"Failed to send email to {recipient_email} via SES: {e}")
        return False


def _send(recipient_email: str, subject: str, text_body: str, html_body: str) -> bool:
    # Read at call time (not import time) so it can be overridden per-request
    # in tests/deploys without reloading the module.
    provider = os.getenv("EMAIL_PROVIDER", "smtp").lower()
    if provider == "ses":
        return _send_via_ses(recipient_email, subject, text_body, html_body)
    return _send_via_smtp(recipient_email, subject, text_body, html_body)


def send_invite_email(
    recipient_email: str,
    invite_token: str,
    app_name: str = "MetOcean Intelligence Platform",
) -> bool:
    """Send invitation email to a new user."""
    app_url = os.getenv("APP_URL", "http://localhost:3000")
    accept_url = f"{app_url}/accept-invite.html?token={invite_token}"
    subject, text_body, html_body = _build_invite_email(app_name, accept_url)
    return _send(recipient_email, subject, text_body, html_body)


def send_password_reset_email(
    recipient_email: str,
    reset_token: str,
    app_name: str = "MetOcean Intelligence Platform",
) -> bool:
    """Send password reset email."""
    app_url = os.getenv("APP_URL", "http://localhost:3000")
    reset_url = f"{app_url}/reset-password.html?token={reset_token}"
    subject, text_body, html_body = _build_reset_email(app_name, reset_url)
    return _send(recipient_email, subject, text_body, html_body)
