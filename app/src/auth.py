import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from src.db import get_db
from src.models import User, UserInvite

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

JWT_SECRET = os.getenv("METOCEAN_JWT_SECRET")
if not JWT_SECRET:
    raise RuntimeError(
        "METOCEAN_JWT_SECRET is not set. Refusing to start with an insecure "
        "default. Generate one with: openssl rand -hex 32"
    )
JWT_ALGORITHM = os.getenv("METOCEAN_JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("METOCEAN_JWT_EXPIRE_MINUTES", "60"))

INVITE_EXPIRE_DAYS = 7


def _as_utc(dt: datetime) -> datetime:
    """Normalize a datetime to tz-aware UTC.

    SQLite (used in tests, and sometimes for quick local runs) doesn't
    persist tzinfo even for DateTime(timezone=True) columns, so values read
    back from the DB can be naive. Treat naive datetimes as UTC.
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt

# Hardcoded admin emails
ADMIN_EMAILS = {
    "kamaluddeen.usman@utp.edu.my",
    "baffaabba2@gmail.com",
}


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(password, hashed_password)


def create_access_token(email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    payload = {
        "sub": email,
        "exp": expire,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, email: str, password: str) -> User:
    if get_user_by_email(db, email) is not None:
        raise ValueError("Email already registered")

    user = User(email=email, hashed_password=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = get_user_by_email(db, email)
    if user is None:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    if not user.is_active:
        return None
    return user


def get_current_user(
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization token",
        )

    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user = get_user_by_email(db, email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account has been deactivated",
        )
    return user


def is_admin(user: User) -> bool:
    """Check if a user is an admin (by email or is_admin flag)."""
    return user.is_admin or user.email in ADMIN_EMAILS


def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Dependency: require admin privileges."""
    if not is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required.",
        )
    return current_user


def create_invite_token() -> str:
    """Generate a secure random token for email invitations."""
    return secrets.token_urlsafe(32)


def create_invitation(db: Session, email: str) -> UserInvite:
    """Create a new invitation for a user, valid for INVITE_EXPIRE_DAYS."""
    token = create_invite_token()
    expires_at = datetime.now(timezone.utc) + timedelta(days=INVITE_EXPIRE_DAYS)
    invite = UserInvite(email=email, token=token, expires_at=expires_at)
    db.add(invite)
    db.commit()
    db.refresh(invite)
    return invite


def get_invitation_by_token(db: Session, token: str) -> Optional[UserInvite]:
    """Retrieve an invitation by token."""
    return db.query(UserInvite).filter(UserInvite.token == token).first()


def accept_invitation(db: Session, token: str, password: str) -> User:
    """Accept an invitation and create the user account."""
    invite = get_invitation_by_token(db, token)
    if not invite:
        raise ValueError("Invalid or expired invitation token")

    if invite.accepted:
        raise ValueError("Invitation already accepted")

    if datetime.now(timezone.utc) > _as_utc(invite.expires_at):
        raise ValueError("Invitation has expired. Ask an admin to resend it.")

    # Create the user
    user = create_user(db, invite.email, password)
    
    # Set admin flag if email is in hardcoded admin list
    if user.email in ADMIN_EMAILS:
        user.is_admin = True
        db.commit()
        db.refresh(user)
    
    # Mark invitation as accepted
    invite.accepted = True
    invite.accepted_at = datetime.now(timezone.utc)
    db.commit()
    
    return user


def get_all_users(db: Session) -> list:
    """Get all users for admin list."""
    return db.query(User).order_by(User.created_at.desc()).all()


def get_pending_invites(db: Session) -> list:
    """Get all pending (not yet accepted) invitations."""
    return db.query(UserInvite).filter(UserInvite.accepted == False).order_by(UserInvite.created_at.desc()).all()


def deactivate_user(db: Session, user_id: int) -> Optional[User]:
    """Deactivate a user, blocking further login and invalidating admin status."""
    user = db.query(User).filter(User.id == user_id).first()
    if user and user.email not in ADMIN_EMAILS:
        # Prevent deactivating hardcoded admins
        user.is_admin = False
        user.is_active = False
        db.commit()
        db.refresh(user)
    return user


# ── Password Reset Functions ─────────────────────────────────────────────────

def create_password_reset_token(db: Session, email: str) -> str:
    """Generate a secure password reset token and save to database."""
    from src.models import PasswordReset
    
    user = get_user_by_email(db, email)
    if not user:
        # Return a dummy token (for security, don't reveal if email exists)
        return secrets.token_urlsafe(32)
    
    token = secrets.token_urlsafe(32)
    expire = datetime.now(timezone.utc) + timedelta(hours=1)
    
    reset = PasswordReset(
        user_id=user.id,
        token=token,
        expires_at=expire
    )
    db.add(reset)
    db.commit()
    db.refresh(reset)
    return token


def get_password_reset_by_token(db: Session, token: str) -> Optional[object]:
    """Retrieve a password reset token if valid and not expired."""
    from src.models import PasswordReset
    
    reset = db.query(PasswordReset).filter(PasswordReset.token == token).first()
    if not reset:
        return None
    
    # Check if token has expired
    if datetime.now(timezone.utc) > _as_utc(reset.expires_at):
        return None
    
    return reset


def use_password_reset_token(db: Session, token: str, new_password: str) -> User:
    """Use a password reset token to update user password and invalidate token."""
    from src.models import PasswordReset
    
    reset = get_password_reset_by_token(db, token)
    if not reset:
        raise ValueError("Invalid or expired password reset token")
    
    user = db.query(User).filter(User.id == reset.user_id).first()
    if not user:
        raise ValueError("User not found")
    
    # Update password
    user.hashed_password = hash_password(new_password)
    db.add(user)
    
    # Delete the used token
    db.delete(reset)
    
    db.commit()
    db.refresh(user)
    return user
