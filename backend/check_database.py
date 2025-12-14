#!/usr/bin/env python3
"""
Database connection and schema checker.
Run this script to verify database setup.
"""
import sys
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def check_database():
    """Check database connection and schema."""
    print("=" * 60)
    print("Database Connection and Schema Checker")
    print("=" * 60)
    
    # Get database URL
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not found in environment variables")
        print("   Please check your .env file")
        return False
    
    print(f"✅ DATABASE_URL found: {database_url}")
    print()
    
    # Try to connect
    try:
        engine = create_engine(database_url)
        print("Attempting to connect to database...")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ Connected to PostgreSQL")
            print(f"   Version: {version}")
            print()
    except Exception as e:
        print(f"❌ Failed to connect to database")
        print(f"   Error: {e}")
        print()
        print("Troubleshooting:")
        print("1. Check if PostgreSQL is running:")
        print("   brew services list | grep postgresql")
        print("2. Start PostgreSQL if needed:")
        print("   brew services start postgresql@15")
        print("3. Check if database exists:")
        print("   psql -l | grep toefl_speaking_dev")
        print("4. Create database if needed:")
        print("   createdb toefl_speaking_dev")
        return False
    
    # Check tables
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"Found {len(tables)} tables:")
        for table in tables:
            print(f"  - {table}")
        print()
        
        # Check practice_sessions table
        if "practice_sessions" not in tables:
            print("❌ practice_sessions table not found")
            print()
            print("Run migrations to create tables:")
            print("  cd backend")
            print("  conda activate rislingo")
            print("  alembic upgrade head")
            return False
        
        print("✅ practice_sessions table exists")
        
        # Check columns
        columns = inspector.get_columns("practice_sessions")
        print(f"\npractice_sessions columns ({len(columns)}):")
        for col in columns:
            nullable = "NULL" if col['nullable'] else "NOT NULL"
            print(f"  - {col['name']}: {col['type']} ({nullable})")
        
        # Check required columns
        required_columns = ['id', 'task_type', 'reading_text', 'lecture_script', 'question']
        column_names = [col['name'] for col in columns]
        
        missing_columns = [col for col in required_columns if col not in column_names]
        if missing_columns:
            print(f"\n❌ Missing required columns: {', '.join(missing_columns)}")
            print("   Run migrations to update schema:")
            print("   alembic upgrade head")
            return False
        
        print("\n✅ All required columns present")
        
    except Exception as e:
        print(f"❌ Failed to inspect database schema")
        print(f"   Error: {e}")
        return False
    
    # Test insert
    try:
        from models import PracticeSession
        from uuid import uuid4
        
        Session = sessionmaker(bind=engine)
        session = Session()
        
        print("\nTesting database insert...")
        test_id = uuid4()
        test_session = PracticeSession(
            id=test_id,
            task_type="task3",
            reading_text="Test reading",
            lecture_script="Test lecture",
            question="Test question"
        )
        session.add(test_session)
        session.commit()
        print(f"✅ Test insert successful (ID: {test_id})")
        
        # Clean up
        session.delete(test_session)
        session.commit()
        print("✅ Test cleanup successful")
        session.close()
        
    except Exception as e:
        print(f"❌ Failed to test database insert")
        print(f"   Error: {e}")
        print(f"   Error type: {type(e).__name__}")
        if session:
            session.rollback()
            session.close()
        return False
    
    print()
    print("=" * 60)
    print("✅ All checks passed! Database is ready.")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = check_database()
    sys.exit(0 if success else 1)

