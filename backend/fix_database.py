#!/usr/bin/env python3
"""
Fix database schema - make user_id nullable in practice_sessions table.
"""
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def fix_database():
    """Fix user_id column to allow NULL values."""
    print("=" * 60)
    print("Database Schema Fix - Make user_id nullable")
    print("=" * 60)
    
    # Get database URL
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not found in environment variables")
        return False
    
    print(f"✅ DATABASE_URL found")
    print()
    
    try:
        engine = create_engine(database_url)
        print("Connecting to database...")
        
        with engine.connect() as conn:
            # Check current state
            print("Checking current schema...")
            result = conn.execute(text("""
                SELECT column_name, is_nullable, data_type
                FROM information_schema.columns
                WHERE table_name = 'practice_sessions' AND column_name = 'user_id'
            """))
            
            row = result.fetchone()
            if row:
                print(f"Current state: user_id is_nullable = {row[1]}")
                
                if row[1] == 'NO':
                    print("\nApplying fix: ALTER TABLE practice_sessions ALTER COLUMN user_id DROP NOT NULL...")
                    conn.execute(text("ALTER TABLE practice_sessions ALTER COLUMN user_id DROP NOT NULL"))
                    conn.commit()
                    print("✅ Successfully modified user_id column to allow NULL")
                else:
                    print("✅ user_id column already allows NULL - no changes needed")
            else:
                print("❌ user_id column not found in practice_sessions table")
                return False
            
            # Verify the change
            print("\nVerifying change...")
            result = conn.execute(text("""
                SELECT column_name, is_nullable, data_type
                FROM information_schema.columns
                WHERE table_name = 'practice_sessions' AND column_name = 'user_id'
            """))
            
            row = result.fetchone()
            if row and row[1] == 'YES':
                print(f"✅ Verified: user_id is_nullable = {row[1]}")
            else:
                print("❌ Verification failed")
                return False
        
        print()
        print("=" * 60)
        print("✅ Database fix completed successfully!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("1. Run: python check_database.py")
        print("2. Restart backend: uvicorn main:app --reload --host 0.0.0.0 --port 8000")
        return True
        
    except Exception as e:
        print(f"❌ Failed to fix database")
        print(f"   Error: {e}")
        print(f"   Error type: {type(e).__name__}")
        return False

if __name__ == "__main__":
    success = fix_database()
    sys.exit(0 if success else 1)

