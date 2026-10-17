"""
Migration: Add missing columns to app_users table.
VidyaMarksheet (Developed at VidyaLabs | Priyanka Kumari)
"""

from sqlalchemy import text
from backend.db.database import sync_engine

def migrate():
    with sync_engine.begin() as conn:
        conn.execute(text("ALTER TABLE app_users ADD COLUMN IF NOT EXISTS email VARCHAR(100);"))
        conn.execute(text("ALTER TABLE app_users ADD COLUMN IF NOT EXISTS created_by VARCHAR(50) DEFAULT 'Admin';"))
    print("Migration completed: app_users now has email and created_by columns.")

if __name__ == "__main__":
    migrate()
