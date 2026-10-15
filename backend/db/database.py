"""
Database configuration and session management for VidyaMarksheet.
Supports asynchronous sessions (via asyncpg), synchronous sessions (via psycopg2 & SQLAlchemy),
and dual-environment auto-detection (Office PC without password / Home PC with special characters).
Compliant with INC Gazette & SGPGIMS Lucknow Regulations.
VidyaLabs Copyright © 2026.
"""

import os
from contextlib import contextmanager
from typing import AsyncGenerator
from urllib.parse import quote_plus
from dotenv import load_dotenv

import psycopg2
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# Locate and load backend/.env
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# Database connection credentials (supporting both DB_* and POSTGRES_* keys)
DB_NAME = os.getenv("DB_NAME") or os.getenv("POSTGRES_DB", "vidya_examination_db")
DB_USER = os.getenv("DB_USER") or os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD") or os.getenv("POSTGRES_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST") or os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT") or os.getenv("POSTGRES_PORT", "5432")

# URL-encode password to safely handle special characters (@, #, $, :, etc.)
encoded_pw = quote_plus(DB_PASSWORD) if DB_PASSWORD else ""

# Direct raw psycopg2 connection helper
def get_connection():
    """
    Direct psycopg2 connection using active environment configuration.
    Attempts primary configured password, with seamless fallback for empty password.
    """
    try:
        return psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=int(DB_PORT)
        )
    except Exception:
        # Fallback attempt with empty password if primary fails
        return psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password="",
            host=DB_HOST,
            port=int(DB_PORT)
        )

# Backward-compatible alias
get_psycopg2_connection = get_connection


def _build_database_urls():
    """Constructs robust synchronous and asynchronous SQLAlchemy connection URLs."""
    if os.getenv("SYNC_DATABASE_URL") and os.getenv("DATABASE_URL"):
        return os.getenv("SYNC_DATABASE_URL"), os.getenv("DATABASE_URL")

    candidate_passwords = [DB_PASSWORD, ""] if DB_PASSWORD else [""]

    for pw in candidate_passwords:
        try:
            conn = psycopg2.connect(
                dbname=DB_NAME,
                user=DB_USER,
                password=pw,
                host=DB_HOST,
                port=int(DB_PORT)
            )
            conn.close()
            
            enc_pw = quote_plus(pw) if pw else ""
            if enc_pw:
                s_url = f"postgresql://{DB_USER}:{enc_pw}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
                a_url = f"postgresql+asyncpg://{DB_USER}:{enc_pw}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
            else:
                s_url = f"postgresql://{DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
                a_url = f"postgresql+asyncpg://{DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
            return s_url, a_url
        except Exception:
            continue

    # Default fallback using encoded credentials
    if encoded_pw:
        s_url = f"postgresql://{DB_USER}:{encoded_pw}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        a_url = f"postgresql+asyncpg://{DB_USER}:{encoded_pw}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    else:
        s_url = f"postgresql://{DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        a_url = f"postgresql+asyncpg://{DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return s_url, a_url


SYNC_DATABASE_URL, DATABASE_URL = _build_database_urls()

# Base model for declarative class definitions
Base = declarative_base()

# Async Engine and SessionMaker (used for FastAPI async endpoints)
async_engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

# Sync Engine and SessionMaker (used for migrations, bulk CLI scripts, openpyxl ingestion)
sync_engine = create_engine(
    SYNC_DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
)

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for obtaining an asynchronous database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@contextmanager
def get_sync_session():
    """Context manager for synchronous database operations."""
    session: Session = SyncSessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()