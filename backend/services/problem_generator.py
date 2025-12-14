"""
Problem Generator Service for TOEFL Speaking Master.
Generates Task 3 problems using GPT-4 and TTS.
"""
import os
import logging
import random
from typing import Optional, Dict, Any
from uuid import uuid4
from datetime import datetime

from services.openai_client import get_openai_client
from exceptions import ProblemGenerationError
from database import get_db
from models import PracticeSession, User
from sqlalchemy.orm import Session


logger = logging.getLogger(__name__)


class ProblemGeneratorService:
    """
    Service for generating TOEFL Task 3 problems.
    
    Generates:
    - Reading passages (academic concepts)
    - Lecture scripts (examples and applications)
    - Questions
    - Audio files for lectures using TTS
    """
    
    # Academic topic categories for Task 3
    TOPIC_CATEGORIES = [
        "psychology",
        "biology",
        "economics",
        "sociology",
        "environmental_science",
        "education",
        "anthropology",
        "business",
        "history",
        "linguistics"
    ]
    
    def __init__(self):
        """Initialize the problem generator service."""
        self.openai_client = get_openai_client()
        self.audio_storage_path = os.getenv("AUDIO_STORAGE_PATH", "backend/audio_files")
        
        # Create audio storage directory if it doesn't exist
        os.makedirs(self.audio_storage_path, exist_ok=True)
        
        logger.info("ProblemGeneratorService initialized")
    
    def _select_random_topic(self) -> str:
        """
        Select a random academic topic category.
        
        Returns:
            Random topic category string
        """
        return random.choice(self.TOPIC_CATEGORIES)
    
    def _get_user_previous_questions(self, user_identifier: str, task_type: str, db: Session, limit: int = 20) -> list:
        """
        Get user's previous questions for the specified task type.
        
        Args:
            user_identifier: User identifier
            task_type: Task type (task1, task2, task3, task4)
            db: Database session
            limit: Maximum number of previous questions to retrieve
            
        Returns:
            List of previous question texts
        """
        try:
            # Find user by identifier
            user = db.query(User).filter(User.user_identifier == user_identifier).first()
            if not user:
                return []
            
            # Query previous sessions for this user and task type
            sessions = db.query(PracticeSession).filter(
                PracticeSession.user_id == user.id,
                PracticeSession.task_type == task_type,
                PracticeSession.question.isnot(None)
            ).order_by(PracticeSession.created_at.desc()).limit(limit).all()
            
            # Extract questions
            previous_questions = [session.question for session in sessions if session.question]
            
            logger.info(f"Found {len(previous_questions)} previous {task_type} questions for user {user_identifier}")
            return previous_questions
            
        except Exception as e:
            logger.error(f"Error fetching previous questions: {e}")
            return []
    
    async def generate_problem(
        self,
        task_type: str = "task3",
        topic_category: Optional[str] = None,
        user_identifier: Optional[str] = None,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Generate a complete TOEFL problem based on task type.
        
        Args:
            task_type: Task type ("task1", "task2", "task3", "task4")
            topic_category: Optional specific topic category
            user_identifier: Optional user identifier for avoiding duplicates
            db: Optional database session for fetching previous questions
            
        Returns:
            Dictionary containing problem data (varies by task type)
                
        Raises:
            ProblemGenerationError: If generation fails
        """
        try:
            # Get previous questions if user_identifier and db are provided
            previous_questions = []
            if user_identifier and db:
                previous_questions = self._get_user_previous_questions(user_identifier, task_type, db)
            
            if task_type == "task1":
                return await self._generate_task1_problem(previous_questions)
            elif task_type == "task2":
                return await self._generate_task2_problem(previous_questions)
            elif task_type == "task3":
                return await self._generate_task3_problem(topic_category, previous_questions)
            elif task_type == "task4":
                return await self._generate_task4_problem(previous_questions)
            else:
                raise ProblemGenerationError(f"Unsupported task type: {task_type}")
            
        except Exception as e:
            logger.error(f"Problem generation failed: {e}")
            raise ProblemGenerationError(f"Failed to generate problem: {str(e)}")
    
    async def _generate_task1_problem(self, previous_questions: list = None) -> Dict[str, Any]:
        """
        Generate a TOEFL Task 1 (Independent Speaking) problem.
        
        Returns:
            Dictionary containing:
                - problem_id: Unique identifier
                - question: Independent question text
                - preparation_time: 15 seconds
                - speaking_time: 45 seconds
        """
        try:
            logger.info("Generating Task 1 problem")
            
            # Generate Task 1 question using GPT-4
            problem_data = await self.openai_client.generate_task1_question(previous_questions or [])
            
            problem_id = str(uuid4())
            
            complete_problem = {
                "problem_id": problem_id,
                "question": problem_data["question"],
                "preparation_time": 15,
                "speaking_time": 45,
                "task_type": "task1",
                "created_at": datetime.now().isoformat()
            }
            
            logger.info(f"Task 1 problem generated successfully: {problem_id}")
            return complete_problem
            
        except Exception as e:
            logger.error(f"Task 1 problem generation failed: {e}")
            raise ProblemGenerationError(f"Failed to generate Task 1 problem: {str(e)}")
    
    async def _generate_task2_problem(self, previous_questions: list = None) -> Dict[str, Any]:
        """
        Generate a TOEFL Task 2 (Integrated Speaking) problem.
        
        Returns:
            Dictionary containing Task 2 problem data
        """
        try:
            logger.info("Generating Task 2 problem")
            
            # Generate Task 2 problem content using GPT-4
            problem_data = await self.openai_client.generate_task2_problem(previous_questions or [])
            
            # Extract components
            announcement_text = problem_data["announcement_text"]
            conversation_script = problem_data["conversation_script"]
            question = problem_data["question"]
            
            # Generate audio for conversation
            problem_id = str(uuid4())
            audio_url = None
            
            try:
                logger.info("Generating conversation audio using TTS")
                audio_bytes = await self.openai_client.generate_speech(
                    text=conversation_script,
                    voice="alloy",
                    speed=0.85  # Slightly slower for clarity (2.2-2.4 words/sec)
                )
                
                # Save audio file
                audio_filename = f"conversation_{problem_id}.mp3"
                audio_filepath = os.path.join(self.audio_storage_path, audio_filename)
                
                with open(audio_filepath, "wb") as f:
                    f.write(audio_bytes)
                
                logger.info(f"Audio saved to: {audio_filepath}")
                
                # Generate audio URL (relative path for now)
                audio_url = f"/audio/{audio_filename}"
                
            except Exception as tts_error:
                logger.warning(f"TTS generation failed for Task 2, continuing without audio: {tts_error}")
                # Continue without audio - the frontend can handle missing audio
            
            # Compile complete problem
            complete_problem = {
                "problem_id": problem_id,
                "reading_text": announcement_text,  # University announcement
                "lecture_script": conversation_script,  # Student conversation
                "lecture_audio_url": audio_url,
                "question": question,
                "topic_category": "campus_announcement",
                "task_type": "task2",
                "created_at": datetime.now().isoformat()
            }
            
            logger.info(f"Task 2 problem generated successfully: {problem_id}")
            return complete_problem
            
        except Exception as e:
            logger.error(f"Task 2 problem generation failed: {e}")
            raise ProblemGenerationError(f"Failed to generate Task 2 problem: {str(e)}")
    
    async def _generate_task4_problem(self, previous_questions: list = None) -> Dict[str, Any]:
        """
        Generate a TOEFL Task 4 (Academic Lecture) problem.
        
        Returns:
            Dictionary containing Task 4 problem data
        """
        try:
            logger.info("Generating Task 4 problem")
            
            # Generate Task 4 problem content using GPT-4
            problem_data = await self.openai_client.generate_task4_problem(previous_questions or [])
            
            # Extract components
            lecture_script = problem_data["lecture_script"]
            question = problem_data["question"]
            
            # Generate audio for lecture
            problem_id = str(uuid4())
            audio_url = None
            
            try:
                logger.info("Generating lecture audio using TTS")
                audio_bytes = await self.openai_client.generate_speech(
                    text=lecture_script,
                    voice="alloy",
                    speed=0.85  # Slightly slower for clarity (2.2-2.4 words/sec)
                )
                
                # Save audio file
                audio_filename = f"lecture_{problem_id}.mp3"
                audio_filepath = os.path.join(self.audio_storage_path, audio_filename)
                
                with open(audio_filepath, "wb") as f:
                    f.write(audio_bytes)
                
                logger.info(f"Audio saved to: {audio_filepath}")
                
                # Generate audio URL (relative path for now)
                audio_url = f"/audio/{audio_filename}"
                
            except Exception as tts_error:
                logger.warning(f"TTS generation failed for Task 4, continuing without audio: {tts_error}")
                # Continue without audio - the frontend can handle missing audio
            
            # Compile complete problem
            complete_problem = {
                "problem_id": problem_id,
                "reading_text": None,  # Task4にはReading不要
                "lecture_script": lecture_script,  # Academic lecture
                "lecture_audio_url": audio_url,
                "question": question,
                "topic_category": "academic_lecture",
                "task_type": "task4",
                "created_at": datetime.now().isoformat()
            }
            
            logger.info(f"Task 4 problem generated successfully: {problem_id}")
            return complete_problem
            
        except Exception as e:
            logger.error(f"Task 4 problem generation failed: {e}")
            raise ProblemGenerationError(f"Failed to generate Task 4 problem: {str(e)}")
    
    async def _generate_task3_problem(self, topic_category: Optional[str] = None, previous_questions: list = None) -> Dict[str, Any]:
        """
        Generate a TOEFL Task 3 problem.
        
        Args:
            topic_category: Optional specific topic category
            
        Returns:
            Dictionary containing Task 3 problem data
        """
        try:
            # Select topic category
            if topic_category is None:
                topic_category = self._select_random_topic()
            elif topic_category not in self.TOPIC_CATEGORIES:
                logger.warning(f"Unknown topic category: {topic_category}, using random")
                topic_category = self._select_random_topic()
            
            logger.info(f"Generating Task 3 problem for topic: {topic_category}")
            
            # Generate problem content using GPT-4
            problem_data = await self.openai_client.generate_problem(
                topic_category=topic_category,
                task_type="task3",
                previous_questions=previous_questions or []
            )
            
            # Extract components
            reading_text = problem_data["reading_text"]
            lecture_script = problem_data["lecture_script"]
            question = problem_data["question"]
            
            # Generate audio for lecture
            problem_id = str(uuid4())
            audio_url = None
            
            try:
                logger.info("Generating lecture audio using TTS")
                audio_bytes = await self.openai_client.generate_speech(
                    text=lecture_script,
                    voice="alloy",
                    speed=0.9  # Slightly slower for clarity
                )
                
                # Save audio file
                audio_filename = f"lecture_{problem_id}.mp3"
                audio_filepath = os.path.join(self.audio_storage_path, audio_filename)
                
                with open(audio_filepath, "wb") as f:
                    f.write(audio_bytes)
                
                logger.info(f"Audio saved to: {audio_filepath}")
                
                # Generate audio URL (relative path for now)
                audio_url = f"/audio/{audio_filename}"
                
            except Exception as tts_error:
                logger.warning(f"TTS generation failed for Task 3, continuing without audio: {tts_error}")
                # Continue without audio - the frontend can handle missing audio
            
            # Compile complete problem
            complete_problem = {
                "problem_id": problem_id,
                "reading_text": reading_text,
                "lecture_script": lecture_script,
                "lecture_audio_url": audio_url,
                "question": question,
                "topic_category": topic_category,
                "task_type": "task3",
                "created_at": datetime.now().isoformat()
            }
            
            logger.info(f"Task 3 problem generated successfully: {problem_id}")
            return complete_problem
            
        except Exception as e:
            logger.error(f"Task 3 problem generation failed: {e}")
            raise ProblemGenerationError(f"Failed to generate Task 3 problem: {str(e)}")
    
    async def generate_lecture_audio(
        self,
        lecture_script: str,
        problem_id: Optional[str] = None
    ) -> str:
        """
        Generate audio file for a lecture script.
        
        Args:
            lecture_script: Text of the lecture
            problem_id: Optional problem ID for filename
            
        Returns:
            Audio file URL/path
            
        Raises:
            ProblemGenerationError: If audio generation fails
        """
        try:
            logger.info("Generating lecture audio")
            
            # Generate audio using TTS
            audio_bytes = await self.openai_client.generate_speech(
                text=lecture_script,
                voice="alloy",
                speed=0.9
            )
            
            # Save audio file
            if problem_id is None:
                problem_id = str(uuid4())
            
            audio_filename = f"lecture_{problem_id}.mp3"
            audio_filepath = os.path.join(self.audio_storage_path, audio_filename)
            
            with open(audio_filepath, "wb") as f:
                f.write(audio_bytes)
            
            logger.info(f"Audio saved to: {audio_filepath}")
            
            # Return audio URL
            audio_url = f"/audio/{audio_filename}"
            return audio_url
            
        except Exception as e:
            logger.error(f"Audio generation failed: {e}")
            raise ProblemGenerationError(f"Failed to generate audio: {str(e)}")


# Singleton instance
_problem_generator: Optional[ProblemGeneratorService] = None


def get_problem_generator() -> ProblemGeneratorService:
    """
    Get or create singleton problem generator instance.
    
    Returns:
        ProblemGeneratorService instance
    """
    global _problem_generator
    if _problem_generator is None:
        _problem_generator = ProblemGeneratorService()
    return _problem_generator
