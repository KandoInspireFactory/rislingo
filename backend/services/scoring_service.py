"""
Scoring service for TOEFL Speaking responses.
Uses GPT-4 to evaluate responses based on TOEFL official rubrics.
"""
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from services.openai_client import get_openai_client
from exceptions import ScoringError


logger = logging.getLogger(__name__)


@dataclass
class ScoringDetail:
    """Detailed scoring information for a single criterion."""
    score: int  # 0-4
    feedback: str


@dataclass
class ScoringResult:
    """Complete scoring result with all criteria."""
    overall_score: int  # 0-4
    delivery: ScoringDetail
    language_use: ScoringDetail
    topic_development: ScoringDetail
    improvement_tips: List[str]


@dataclass
class HighlightedPhrase:
    """A highlighted phrase in the model answer."""
    text: str
    category: str  # 'transition', 'example', 'conclusion'
    useful_for_writing: bool


@dataclass
class ModelAnswer:
    """Model answer with highlighted phrases."""
    model_answer: str
    highlighted_phrases: List[HighlightedPhrase]


class ScoringService:
    """
    Service for scoring TOEFL Speaking responses.
    
    Uses GPT-4 to evaluate responses based on three criteria:
    - Delivery: Clarity, fluency, pronunciation, pacing
    - Language Use: Grammar, vocabulary, sentence structure
    - Topic Development: Content accuracy, completeness, coherence
    
    Each criterion is scored on a 0-4 scale according to TOEFL rubrics.
    """
    
    def __init__(self):
        """Initialize scoring service with OpenAI client."""
        self.openai_client = get_openai_client()
        logger.info("ScoringService initialized")
    
    async def evaluate_task1_response(
        self,
        transcript: str,
        question: str
    ) -> Dict[str, Any]:
        """
        Evaluate a TOEFL Speaking Task 1 response.
        
        Args:
            transcript: User's transcribed response
            question: The question asked
            
        Returns:
            Dictionary with overall score and feedback
            
        Raises:
            ScoringError: If scoring fails
        """
        try:
            logger.info("Starting Task 1 response evaluation")
            
            # Validate inputs
            if not transcript or not transcript.strip():
                raise ScoringError("Transcript cannot be empty")
            if not question or not question.strip():
                raise ScoringError("Question cannot be empty")
            
            # Call OpenAI client to score the Task 1 response
            scoring_data = await self.openai_client.score_task1_response(
                transcript=transcript,
                question=question
            )
            
            logger.info(f"Task 1 response evaluation completed (overall score: {scoring_data.get('overall_score')})")
            return scoring_data
            
        except ScoringError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during Task 1 scoring: {e}")
            raise ScoringError(f"Failed to evaluate Task 1 response: {str(e)}")

    async def evaluate_response(
        self,
        transcript: str,
        reading_text: Optional[str],
        lecture_script: str,
        question: str
    ) -> ScoringResult:
        """
        Evaluate a TOEFL Speaking Task 3 response.
        
        Args:
            transcript: User's transcribed response
            reading_text: Original reading passage
            lecture_script: Original lecture script
            question: The question asked
            
        Returns:
            ScoringResult with scores and feedback for all criteria
            
        Raises:
            ScoringError: If scoring fails
        """
        try:
            logger.info("Starting response evaluation")
            
            # Validate inputs
            if not transcript or not transcript.strip():
                raise ScoringError("Transcript cannot be empty")
            # reading_text is optional for Task4
            if reading_text is not None and not reading_text.strip():
                raise ScoringError("Reading text cannot be empty when provided")
            if not lecture_script or not lecture_script.strip():
                raise ScoringError("Lecture script cannot be empty")
            if not question or not question.strip():
                raise ScoringError("Question cannot be empty")
            
            # Call OpenAI client to score the response
            scoring_data = await self.openai_client.score_response(
                transcript=transcript,
                reading_text=reading_text,
                lecture_script=lecture_script,
                question=question
            )
            
            # Parse and validate scoring data
            result = self._parse_scoring_data(scoring_data)
            
            logger.info(f"Response evaluation completed (overall score: {result.overall_score})")
            return result
            
        except ScoringError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during scoring: {e}")
            raise ScoringError(f"Failed to evaluate response: {str(e)}")
    
    def _parse_scoring_data(self, data: Dict[str, Any]) -> ScoringResult:
        """
        Parse and validate scoring data from OpenAI response.
        
        Args:
            data: Raw scoring data from OpenAI
            
        Returns:
            Validated ScoringResult
            
        Raises:
            ScoringError: If data is invalid
        """
        try:
            # Validate and extract scores
            delivery_score = self._validate_score(data.get("delivery_score"), "delivery_score")
            language_use_score = self._validate_score(data.get("language_use_score"), "language_use_score")
            topic_dev_score = self._validate_score(data.get("topic_dev_score"), "topic_dev_score")
            overall_score = self._validate_score(data.get("overall_score"), "overall_score")
            
            # Extract feedback
            delivery_feedback = data.get("delivery_feedback", "")
            language_use_feedback = data.get("language_use_feedback", "")
            topic_dev_feedback = data.get("topic_dev_feedback", "")
            
            # Validate feedback is not empty
            if not delivery_feedback:
                raise ScoringError("Missing delivery feedback")
            if not language_use_feedback:
                raise ScoringError("Missing language use feedback")
            if not topic_dev_feedback:
                raise ScoringError("Missing topic development feedback")
            
            # Extract improvement tips
            improvement_tips = data.get("improvement_tips", [])
            if not isinstance(improvement_tips, list):
                raise ScoringError("Improvement tips must be a list")
            if not improvement_tips:
                raise ScoringError("At least one improvement tip is required")
            
            # Create scoring result
            return ScoringResult(
                overall_score=overall_score,
                delivery=ScoringDetail(
                    score=delivery_score,
                    feedback=delivery_feedback
                ),
                language_use=ScoringDetail(
                    score=language_use_score,
                    feedback=language_use_feedback
                ),
                topic_development=ScoringDetail(
                    score=topic_dev_score,
                    feedback=topic_dev_feedback
                ),
                improvement_tips=improvement_tips
            )
            
        except ScoringError:
            raise
        except Exception as e:
            logger.error(f"Failed to parse scoring data: {e}")
            raise ScoringError(f"Invalid scoring data format: {str(e)}")
    
    def _validate_score(self, score: Any, field_name: str) -> int:
        """
        Validate that a score is an integer in the range 0-4.
        
        Args:
            score: Score value to validate
            field_name: Name of the field (for error messages)
            
        Returns:
            Validated score as integer
            
        Raises:
            ScoringError: If score is invalid
        """
        if score is None:
            raise ScoringError(f"Missing required field: {field_name}")
        
        # Convert to int if it's a float
        if isinstance(score, float):
            score = int(score)
        
        if not isinstance(score, int):
            raise ScoringError(f"Invalid score type for {field_name}: expected int, got {type(score)}")
        
        if score < 0 or score > 4:
            raise ScoringError(f"Score for {field_name} must be between 0 and 4, got {score}")
        
        return score
    
    async def generate_task1_model_answer(
        self,
        question: str
    ) -> Dict[str, Any]:
        """
        Generate a model answer for a TOEFL Speaking Task 1 question.
        
        Args:
            question: The question asked
            
        Returns:
            Dictionary with model answer and highlighted phrases
            
        Raises:
            ScoringError: If model answer generation fails
        """
        try:
            logger.info("Starting Task 1 model answer generation")
            
            # Validate inputs
            if not question or not question.strip():
                raise ScoringError("Question cannot be empty")
            
            # Call OpenAI client to generate Task 1 model answer
            model_data = await self.openai_client.generate_task1_model_answer(
                question=question
            )
            
            logger.info("Task 1 model answer generation completed")
            return model_data
            
        except ScoringError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during Task 1 model answer generation: {e}")
            raise ScoringError(f"Failed to generate Task 1 model answer: {str(e)}")

    async def generate_task2_model_answer(
        self,
        announcement_text: str,
        conversation_script: str,
        question: str
    ) -> Dict[str, Any]:
        """
        Generate a model answer for a TOEFL Speaking Task 2 question.
        
        Args:
            announcement_text: University announcement text
            conversation_script: Student conversation script
            question: The question asked
            
        Returns:
            Dictionary with model answer and highlighted phrases
            
        Raises:
            ScoringError: If model answer generation fails
        """
        try:
            logger.info("Starting Task 2 model answer generation")
            
            # Validate inputs
            if not announcement_text or not announcement_text.strip():
                raise ScoringError("Announcement text cannot be empty")
            if not conversation_script or not conversation_script.strip():
                raise ScoringError("Conversation script cannot be empty")
            if not question or not question.strip():
                raise ScoringError("Question cannot be empty")
            
            # Call OpenAI client to generate Task 2 model answer
            model_data = await self.openai_client.generate_task2_model_answer(
                announcement_text=announcement_text,
                conversation_script=conversation_script,
                question=question
            )
            
            logger.info("Task 2 model answer generation completed")
            return model_data
            
        except ScoringError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during Task 2 model answer generation: {e}")
            raise ScoringError(f"Failed to generate Task 2 model answer: {str(e)}")

    async def generate_model_answer(
        self,
        reading_text: Optional[str],
        lecture_script: str,
        question: str
    ) -> ModelAnswer:
        """
        Generate a model answer for a TOEFL Speaking Task 3 or Task 4 question.
        
        Args:
            reading_text: Original reading passage (None for Task 4)
            lecture_script: Original lecture script
            question: The question asked
            
        Returns:
            ModelAnswer with text and highlighted phrases
            
        Raises:
            ScoringError: If model answer generation fails
        """
        try:
            logger.info("Starting model answer generation")
            
            # Validate inputs
            # reading_text is optional for Task4
            if reading_text is not None and not reading_text.strip():
                raise ScoringError("Reading text cannot be empty when provided")
            if not lecture_script or not lecture_script.strip():
                raise ScoringError("Lecture script cannot be empty")
            if not question or not question.strip():
                raise ScoringError("Question cannot be empty")
            
            # Call OpenAI client to generate model answer
            model_data = await self.openai_client.generate_model_answer(
                reading_text=reading_text,
                lecture_script=lecture_script,
                question=question
            )
            
            # Parse and validate model answer data
            result = self._parse_model_answer_data(model_data)
            
            logger.info("Model answer generation completed")
            return result
            
        except ScoringError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during model answer generation: {e}")
            raise ScoringError(f"Failed to generate model answer: {str(e)}")
    
    def _parse_model_answer_data(self, data: Dict[str, Any]) -> ModelAnswer:
        """
        Parse and validate model answer data from OpenAI response.
        
        Args:
            data: Raw model answer data from OpenAI
            
        Returns:
            Validated ModelAnswer
            
        Raises:
            ScoringError: If data is invalid
        """
        try:
            # Extract model answer text
            model_answer_text = data.get("model_answer", "")
            if not model_answer_text:
                raise ScoringError("Missing model answer text")
            
            # Extract and parse highlighted phrases
            highlighted_phrases_data = data.get("highlighted_phrases", [])
            if not isinstance(highlighted_phrases_data, list):
                raise ScoringError("Highlighted phrases must be a list")
            
            highlighted_phrases = []
            for phrase_data in highlighted_phrases_data:
                if not isinstance(phrase_data, dict):
                    logger.warning(f"Skipping invalid phrase data: {phrase_data}")
                    continue
                
                text = phrase_data.get("text", "")
                category = phrase_data.get("category", "")
                useful_for_writing = phrase_data.get("useful_for_writing", False)
                
                # Validate category
                valid_categories = ["transition", "example", "conclusion"]
                if category not in valid_categories:
                    logger.warning(f"Invalid category '{category}', defaulting to 'example'")
                    category = "example"
                
                if text:  # Only add if text is not empty
                    highlighted_phrases.append(
                        HighlightedPhrase(
                            text=text,
                            category=category,
                            useful_for_writing=bool(useful_for_writing)
                        )
                    )
            
            # Create model answer
            return ModelAnswer(
                model_answer=model_answer_text,
                highlighted_phrases=highlighted_phrases
            )
            
        except ScoringError:
            raise
        except Exception as e:
            logger.error(f"Failed to parse model answer data: {e}")
            raise ScoringError(f"Invalid model answer data format: {str(e)}")

    async def generate_ai_review(
        self,
        task_type: str,
        user_transcript: str,
        question: str,
        reading_text: Optional[str] = None,
        lecture_script: Optional[str] = None,
        announcement_text: Optional[str] = None,
        conversation_script: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate AI review for user's response with personalized feedback.
        
        Args:
            task_type: Task type (task1, task2, task3, task4)
            user_transcript: User's transcribed response
            question: The question asked
            reading_text: Reading passage (for task2/task3)
            lecture_script: Lecture script (for task2/task3/task4)
            announcement_text: Announcement text (for task2)
            conversation_script: Conversation script (for task2)
            
        Returns:
            Dictionary with AI review feedback
            
        Raises:
            ScoringError: If AI review generation fails
        """
        try:
            logger.info(f"Starting AI review generation for {task_type}")
            
            # Validate inputs
            if not user_transcript or not user_transcript.strip():
                raise ScoringError("User transcript cannot be empty")
            if not question or not question.strip():
                raise ScoringError("Question cannot be empty")
            if task_type not in ["task1", "task2", "task3", "task4"]:
                raise ScoringError("Invalid task type")
            
            # Call OpenAI client to generate AI review
            review_data = await self.openai_client.generate_ai_review(
                task_type=task_type,
                user_transcript=user_transcript,
                question=question,
                reading_text=reading_text,
                lecture_script=lecture_script,
                announcement_text=announcement_text,
                conversation_script=conversation_script
            )
            
            logger.info(f"AI review generation completed for {task_type}")
            return review_data
            
        except ScoringError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during AI review generation: {e}")
            raise ScoringError(f"Failed to generate AI review: {str(e)}")


# Singleton instance
_scoring_service = None


def get_scoring_service() -> ScoringService:
    """
    Get or create singleton scoring service instance.
    
    Returns:
        ScoringService instance
    """
    global _scoring_service
    if _scoring_service is None:
        _scoring_service = ScoringService()
    return _scoring_service
