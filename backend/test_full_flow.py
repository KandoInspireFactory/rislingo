#!/usr/bin/env python3
"""
Test the complete flow without calling OpenAI APIs.
This validates the database operations and data flow.
"""
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
from uuid import uuid4
from models import PracticeSession

# Load environment variables
load_dotenv()

def test_full_flow():
    """Test the complete flow: create session -> update with scores."""
    print("=" * 60)
    print("Full Flow Test (No API calls)")
    print("=" * 60)
    
    # Get database URL
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not found")
        return False
    
    print("✅ DATABASE_URL found")
    print()
    
    try:
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Step 1: Create practice session (simulating problem generation)
        print("Step 1: Creating practice session (simulating /api/problems/generate)...")
        test_id = uuid4()
        practice_session = PracticeSession(
            id=test_id,
            user_id=None,  # This should now work!
            task_type="task3",
            reading_text="Test reading passage about biology.",
            lecture_script="Test lecture script explaining the concept.",
            question="Test question asking to summarize the lecture."
        )
        session.add(practice_session)
        session.commit()
        print(f"✅ Practice session created with ID: {test_id}")
        print(f"   user_id: {practice_session.user_id} (NULL is OK)")
        print()
        
        # Step 2: Retrieve session (simulating /api/scoring/evaluate lookup)
        print("Step 2: Retrieving practice session (simulating scoring lookup)...")
        retrieved_session = session.query(PracticeSession).filter(PracticeSession.id == test_id).first()
        
        if not retrieved_session:
            print("❌ Failed to retrieve practice session")
            return False
        
        print(f"✅ Practice session retrieved: {retrieved_session.id}")
        print(f"   task_type: {retrieved_session.task_type}")
        print(f"   question: {retrieved_session.question[:50]}...")
        print()
        
        # Step 3: Update session with scores (simulating scoring completion)
        print("Step 3: Updating session with scores (simulating scoring completion)...")
        retrieved_session.user_transcript = "This is a test transcript of the user's response."
        retrieved_session.overall_score = 3
        retrieved_session.delivery_score = 3
        retrieved_session.language_use_score = 3
        retrieved_session.topic_dev_score = 3
        retrieved_session.feedback_json = {
            "delivery_feedback": "Good delivery",
            "language_use_feedback": "Good language use",
            "topic_dev_feedback": "Good topic development",
            "improvement_tips": ["Practice more", "Use more examples"]
        }
        session.commit()
        print("✅ Session updated with scores")
        print(f"   overall_score: {retrieved_session.overall_score}")
        print()
        
        # Step 4: Retrieve again to verify
        print("Step 4: Verifying update...")
        final_session = session.query(PracticeSession).filter(PracticeSession.id == test_id).first()
        
        if not final_session:
            print("❌ Failed to retrieve updated session")
            return False
        
        if final_session.overall_score != 3:
            print(f"❌ Score not updated correctly: {final_session.overall_score}")
            return False
        
        print("✅ Session update verified")
        print(f"   overall_score: {final_session.overall_score}")
        print(f"   user_transcript: {final_session.user_transcript[:50]}...")
        print()
        
        # Cleanup
        print("Cleaning up test data...")
        session.delete(final_session)
        session.commit()
        print("✅ Test data cleaned up")
        session.close()
        
        print()
        print("=" * 60)
        print("✅ All flow tests passed!")
        print("=" * 60)
        print()
        print("The complete flow works:")
        print("1. ✅ Create practice session without user_id")
        print("2. ✅ Retrieve session by problem_id")
        print("3. ✅ Update session with scores")
        print("4. ✅ Verify updates")
        print()
        print("You can now safely use the application!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed")
        print(f"   Error: {e}")
        print(f"   Error type: {type(e).__name__}")
        if 'session' in locals():
            session.rollback()
            session.close()
        return False

if __name__ == "__main__":
    success = test_full_flow()
    sys.exit(0 if success else 1)

