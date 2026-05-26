"""
Email service for sending invitations and notifications via AWS SES.
"""

import logging
import os
from typing import Optional

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger("metocean.email")

# AWS SES Configuration
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "noreply@metoceanai.com")
APP_URL = os.getenv("APP_URL", "http://localhost:3000")


def get_ses_client():
    """Create and return AWS SES client."""
    if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
        logger.warning("AWS credentials not configured. Email sending disabled.")
        return None
    
    return boto3.client(
        "ses",
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )


def send_invite_email(
    recipient_email: str,
    invite_token: str,
    app_name: str = "MetOcean Intelligence Platform",
) -> bool:
    """
    Send invitation email to a new user.
    
    Args:
        recipient_email: Email address of invitee
        invite_token: Unique token for accepting invite
        app_name: Name of application
        
    Returns:
        True if email sent successfully, False otherwise
    """
    client = get_ses_client()
    if not client:
        logger.error("Cannot send email: AWS SES not configured")
        return False
    
    accept_url = f"{APP_URL}/accept-invite.html?token={invite_token}"
    
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
    
    try:
        response = client.send_email(
            Source=SENDER_EMAIL,
            Destination={"ToAddresses": [recipient_email]},
            Message={
                "Subject": {"Data": subject},
                "Body": {
                    "Text": {"Data": text_body},
                    "Html": {"Data": html_body},
                },
            },
        )
        logger.info(f"Invitation email sent to {recipient_email}. MessageId: {response['MessageId']}")
        return True
    except ClientError as e:
        logger.error(f"Failed to send email to {recipient_email}: {e}")
        return False


def send_password_reset_email(
    recipient_email: str,
    reset_token: str,
    app_name: str = "MetOcean Intelligence Platform",
) -> bool:
    """Send password reset email (placeholder for future use)."""
    client = get_ses_client()
    if not client:
        logger.error("Cannot send email: AWS SES not configured")
        return False
    
    reset_url = f"{APP_URL}/reset-password.html?token={reset_token}"
    
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
    
    try:
        response = client.send_email(
            Source=SENDER_EMAIL,
            Destination={"ToAddresses": [recipient_email]},
            Message={
                "Subject": {"Data": subject},
                "Body": {"Html": {"Data": html_body}},
            },
        )
        logger.info(f"Password reset email sent to {recipient_email}")
        return True
    except ClientError as e:
        logger.error(f"Failed to send password reset email to {recipient_email}: {e}")
        return False
