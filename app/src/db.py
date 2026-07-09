import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "127.0.0.1")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "metocean")
POSTGRES_USER = os.getenv("POSTGRES_USER", "metocean")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "metocean")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    (
        f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@"
        f"{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    ),
)

engine = create_engine(
    DATABASE_URL,
    future=True,
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    # Import here to avoid circular imports between models and Base.
    from app.src.models import User, PasswordReset  # noqa: F401
    from app.src.auth import ADMIN_EMAILS, hash_password

    Base.metadata.create_all(bind=engine)
    
    # Initialize hardcoded admin users if they don't exist
    db = SessionLocal()
    try:
        for admin_email in ADMIN_EMAILS:
            existing = db.query(User).filter(User.email == admin_email).first()
            if not existing:
                # Create admin with a secure random password (they can reset via forgot password)
                import secrets
                temp_password = secrets.token_urlsafe(16)
                admin_user = User(
                    email=admin_email,
                    hashed_password=hash_password(temp_password),
                    is_admin=True
                )
                db.add(admin_user)
                import logging
                logger = logging.getLogger("metocean.db")
                logger.info(f"✓ Initialized admin user: {admin_email}")
        db.commit()
    finally:
        db.close()
