"""
Database Migration Script: Enterprise User Management Lifecycle Enhancement.
Compliant with INC Gazette & SGPGIMS Lucknow Regulations.
Branding: VidyaMarksheet (Developed at VidyaLabs | Priyanka Kumari)
"""

import os
import sys
from sqlalchemy import text

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.db.database import sync_engine
from backend.db.models import AppUser
from backend.security import hash_password
from sqlalchemy.orm import Session


def run_migration():
    print("[MIGRATION] Running User Management Lifecycle Schema Migration...")
    with sync_engine.connect() as conn:
        # Check and add columns on app_users if not existing
        alter_statements = [
            "ALTER TABLE app_users ADD COLUMN IF NOT EXISTS email VARCHAR(100);",
            "ALTER TABLE app_users ADD COLUMN IF NOT EXISTS role VARCHAR(30) NOT NULL DEFAULT 'Viewer';",
            "ALTER TABLE app_users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;",
            "ALTER TABLE app_users ADD COLUMN IF NOT EXISTS must_change_password BOOLEAN DEFAULT TRUE;",
            "ALTER TABLE app_users ADD COLUMN IF NOT EXISTS token_version INT DEFAULT 1;",
            "ALTER TABLE app_users ADD COLUMN IF NOT EXISTS created_by VARCHAR(50) DEFAULT 'Admin';",
            "ALTER TABLE app_users ADD COLUMN IF NOT EXISTS failed_login_attempts INT DEFAULT 0;",
            "ALTER TABLE app_users ADD COLUMN IF NOT EXISTS locked_until TIMESTAMP WITH TIME ZONE;",
            "ALTER TABLE app_users ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();",
            "ALTER TABLE app_users ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMP WITH TIME ZONE;",
            "CREATE INDEX IF NOT EXISTS idx_users_username ON app_users(username);",
        ]
        for stmt in alter_statements:
            try:
                conn.execute(text(stmt))
            except Exception as e:
                print(f"[MIGRATION WARNING] Error executing '{stmt}': {e}")
        conn.commit()
        print("[MIGRATION] Table 'app_users' schema verified/updated.")

    # Ensure root Admin user exists with correct attributes
    with Session(sync_engine) as session:
        admin_user = session.query(AppUser).filter(AppUser.username == "Admin").first()
        if not admin_user:
            print("[MIGRATION] Creating root Admin account...")
            admin_user = AppUser(
                username="Admin",
                full_name="System Administrator",
                email="admin@vidyamarksheet.edu",
                role="Admin",
                hashed_password=hash_password("Admin"),
                is_active=True,
                must_change_password=False,
                token_version=1,
                created_by="SYSTEM",
            )
            session.add(admin_user)
            session.commit()
            print("[MIGRATION] Root Admin account created successfully.")
        else:
            print("[MIGRATION] Root Admin account exists. Ensuring is_active=True, must_change_password=False...")
            admin_user.role = "Admin"
            admin_user.is_active = True
            admin_user.must_change_password = False
            session.commit()
            print("[MIGRATION] Root Admin account state synchronized.")

    print("[MIGRATION] User management migration completed successfully.")


if __name__ == "__main__":
    run_migration()
