"""
Database Migration Script: Enterprise Hardened RBAC, User Accounts & Security Audit Log.
Compliant with INC Gazette & SGPGIMS Lucknow Regulations.
Branding: VidyaMarksheet (Developed at VidyaLabs | Priyanka Kumari)
"""

import os
import sys
from sqlalchemy import text

# Ensure base dir in path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.db.database import sync_engine, Base
from backend.db.models import AppUser, AuthSecurityAuditLog
from backend.db.init_db import seed_default_users


def run_migration():
    print("[MIGRATION] Running Enterprise RBAC & Security Audit Schema Migration...")
    try:
        with sync_engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS app_users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    full_name VARCHAR(150) NOT NULL,
                    hashed_password VARCHAR(255) NOT NULL,
                    role VARCHAR(30) NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    must_change_password BOOLEAN DEFAULT TRUE,
                    failed_login_attempts INT DEFAULT 0,
                    locked_until TIMESTAMP WITH TIME ZONE,
                    token_version INT DEFAULT 1,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    last_login_at TIMESTAMP WITH TIME ZONE
                );

                CREATE TABLE IF NOT EXISTS auth_security_audit_log (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50),
                    action VARCHAR(50) NOT NULL,
                    ip_address VARCHAR(50),
                    user_agent TEXT,
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );

                CREATE INDEX IF NOT EXISTS idx_users_username ON app_users(username);
                CREATE INDEX IF NOT EXISTS idx_auth_audit_user ON auth_security_audit_log(username);
                CREATE INDEX IF NOT EXISTS idx_auth_audit_time ON auth_security_audit_log(timestamp);
            """))
            conn.commit()
            print("[MIGRATION] PostgreSQL app_users and auth_security_audit_log created/verified.")
    except Exception as e:
        print(f"[MIGRATION WARNING] Skipping direct PG migration: {e}")

    try:
        Base.metadata.create_all(bind=sync_engine)
        print("[MIGRATION] SQLAlchemy Base metadata synchronized.")
    except Exception as e:
        print(f"[MIGRATION WARNING] Base.metadata.create_all skipped: {e}")

    # Seed default institutional users
    seed_default_users()
    print("[MIGRATION] Default institutional accounts verified and seeded.")


if __name__ == "__main__":
    run_migration()
