"""
OpenAI API client for TOEFL Speaking Master.
Provides integration with GPT-4, Whisper, and TTS APIs.
"""
import os
import json
import logging
from typing import Optional, List, Dict, Any
from openai import AsyncOpenAI, AsyncAzureOpenAI, OpenAIError, RateLimitError, APIError, APITimeoutError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

from exceptions import ExternalAPIError, SpeechProcessingError, ScoringError, ProblemGenerationError


# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class OpenAIClient:
    """
    OpenAI API client with error handling, retry logic, and rate limiting.
    
    Supports:
    - GPT-4 for problem generation, scoring, and model answers
    - Whisper for speech-to-text transcription
    - TTS for text-to-speech audio generation
    - Azure OpenAI Service integration
    """
    
    def __init__(self, api_key: Optional[str] = None, timeout: int = 30):
        """
        Initialize OpenAI client (Azure or Standard).
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            timeout: Request timeout in seconds (default: 30)
        """
        self.timeout = timeout
        
        # Check for Azure configuration
        self.azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.azure_api_version = os.getenv("AZURE_API_VERSION", "2024-02-15-preview")
        
        if self.azure_api_key and self.azure_endpoint:
            self.is_azure = True
            logger.info("Initializing Azure OpenAI Client")
            self.client = AsyncAzureOpenAI(
                api_key=self.azure_api_key,
                api_version=self.azure_api_version,
                azure_endpoint=self.azure_endpoint,
                timeout=timeout
            )
            # Azure Deployment Names (model parameter in client calls maps to deployment name)
            self.gpt4_model = os.getenv("AZURE_GPT_DEPLOYMENT", "gpt-4")
            self.whisper_model = os.getenv("AZURE_WHISPER_DEPLOYMENT", "whisper") 
            self.tts_model = os.getenv("AZURE_TTS_DEPLOYMENT", "tts")
            self.tts_voice = "alloy" # Azure TTS voices generally match OpenAI names
        else:
            self.is_azure = False
            self.api_key = api_key or os.getenv("OPENAI_API_KEY")
            if not self.api_key:
                raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY or AZURE_OPENAI_API_KEY environment variable.")
            
            logger.info("Initializing Standard OpenAI Client")
            self.client = AsyncOpenAI(
                api_key=self.api_key,
                timeout=timeout
            )
            
            # Model configurations
            self.gpt4_model = "gpt-4"
            self.whisper_model = "whisper-1"
            self.tts_model = "tts-1"
            self.tts_voice = "alloy"
        
        logger.info(f"OpenAI client initialized successfully (Azure: {self.is_azure})")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((RateLimitError, APITimeoutError, APIError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True
    )
    async def call_gpt4(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Call GPT-4 API with retry logic.
        
        Args:
            prompt: User prompt
            system_message: Optional system message for context
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens in response
            
        Returns:
            Generated text response
            
        Raises:
            ExternalAPIError: If API call fails after retries
        """
        try:
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": prompt})
            
            logger.info(f"Calling GPT-4 API (temperature={temperature})")
            
            response = await self.client.chat.completions.create(
                model=self.gpt4_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            result = response.choices[0].message.content
            logger.info("GPT-4 API call successful")
            return result
            
        except RateLimitError as e:
            logger.warning(f"Rate limit exceeded: {e}")
            raise ExternalAPIError("OpenAI", "Rate limit exceeded. Please try again later.")
        except APITimeoutError as e:
            logger.error(f"API timeout: {e}")
            raise ExternalAPIError("OpenAI", "Request timed out. Please try again.")
        except APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise ExternalAPIError("OpenAI", f"API error: {str(e)}")
        except OpenAIError as e:
            logger.error(f"OpenAI error: {e}")
            raise ExternalAPIError("OpenAI", f"Unexpected error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in GPT-4 call: {e}")
            raise ExternalAPIError("OpenAI", f"Unexpected error: {str(e)}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((RateLimitError, APITimeoutError, APIError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True
    )
    async def transcribe_audio(
        self,
        audio_file: bytes,
        filename: str = "audio.mp3",
        language: str = "en"
    ) -> str:
        """
        Transcribe audio using Whisper API with retry logic.
        
        Args:
            audio_file: Audio file bytes
            filename: Filename for the audio
            language: Language code (default: "en")
            
        Returns:
            Transcribed text
            
        Raises:
            SpeechProcessingError: If transcription fails after retries
        """
        try:
            logger.info(f"Calling Whisper API for transcription (language={language}, filename={filename}, size={len(audio_file)} bytes)")
            
            # Validate audio file size and content
            if len(audio_file) == 0:
                raise SpeechProcessingError("Audio file is empty")
            
            if len(audio_file) < 100:
                logger.warning(f"Audio file is very small ({len(audio_file)} bytes), transcription may fail")
            
            # Create a file-like object from bytes
            from io import BytesIO
            audio_buffer = BytesIO(audio_file)
            audio_buffer.name = filename
            
            response = await self.client.audio.transcriptions.create(
                model=self.whisper_model,
                file=audio_buffer,
                language=language
            )
            
            transcript = response.text
            logger.info(f"Whisper API call successful (transcript length: {len(transcript)})")
            return transcript
            
        except RateLimitError as e:
            logger.warning(f"Rate limit exceeded: {e}")
            raise SpeechProcessingError("Rate limit exceeded. Please try again later.")
        except APITimeoutError as e:
            logger.error(f"API timeout: {e}")
            raise SpeechProcessingError("Request timed out. Please try again.")
        except APIError as e:
            logger.error(f"Whisper API error: {e}")
            logger.error(f"Audio file details - filename: {filename}, size: {len(audio_file)} bytes")
            
            # Check if it's a file format error
            error_message = str(e)
            if "Invalid file format" in error_message or "file format" in error_message.lower():
                raise SpeechProcessingError(f"音声ファイルの形式が無効です。サポートされている形式: MP3, WAV, WebM, OGG, FLAC, M4A。エラー詳細: {str(e)}")
            else:
                raise SpeechProcessingError(f"音声の文字起こしに失敗しました: {str(e)}")
        except OpenAIError as e:
            logger.error(f"OpenAI error: {e}")
            raise SpeechProcessingError(f"Unexpected error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in transcription: {e}")
            raise SpeechProcessingError(f"Unexpected error: {str(e)}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((RateLimitError, APITimeoutError, APIError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True
    )
    async def generate_speech(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: float = 1.0
    ) -> bytes:
        """
        Generate speech audio using TTS API with retry logic.
        
        Args:
            text: Text to convert to speech
            voice: Voice to use (alloy, echo, fable, onyx, nova, shimmer)
            speed: Speech speed (0.25 to 4.0)
            
        Returns:
            Audio file bytes (MP3 format)
            
        Raises:
            ExternalAPIError: If TTS generation fails after retries
        """
        try:
            voice = voice or self.tts_voice
            logger.info(f"Calling TTS API (voice={voice}, speed={speed})")
            
            response = await self.client.audio.speech.create(
                model=self.tts_model,
                voice=voice,
                input=text,
                speed=speed
            )
            
            # Read audio bytes from response
            audio_bytes = response.content
            logger.info(f"TTS API call successful (audio size: {len(audio_bytes)} bytes)")
            return audio_bytes
            
        except RateLimitError as e:
            logger.warning(f"Rate limit exceeded: {e}")
            raise ExternalAPIError("OpenAI TTS", "Rate limit exceeded. Please try again later.")
        except APITimeoutError as e:
            logger.error(f"API timeout: {e}")
            raise ExternalAPIError("OpenAI TTS", "Request timed out. Please try again.")
        except APIError as e:
            logger.error(f"TTS API error: {e}")
            raise ExternalAPIError("OpenAI TTS", f"TTS generation failed: {str(e)}")
        except OpenAIError as e:
            logger.error(f"OpenAI error: {e}")
            raise ExternalAPIError("OpenAI TTS", f"Unexpected error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in TTS generation: {e}")
            raise ExternalAPIError("OpenAI TTS", f"Unexpected error: {str(e)}")
    
    async def generate_task4_problem(self, previous_questions: list = None) -> Dict[str, str]:
        """
        Generate TOEFL Task 4 (Academic Lecture) problem using GPT-4.
        
        Args:
            previous_questions: List of previously generated questions to avoid duplicates
        
        Returns:
            Dictionary with lecture_script and question
            
        Raises:
            ProblemGenerationError: If problem generation fails
        """
        system_message = """You are an expert TOEFL iBT test creator specializing in Task 4 (Academic Lecture) questions.
Generate authentic academic lecture content that matches official TOEFL standards."""
        
        # Build previous questions context
        previous_context = ""
        if previous_questions:
            previous_context = f"""
IMPORTANT: Avoid generating content similar to these previously used questions:
{chr(10).join(f"- {q}" for q in previous_questions[-10:])}

Make sure your new lecture topic and question are distinctly different from previous ones.
"""

        prompt = f"""Create a TOEFL Speaking Task 4 (Academic Lecture) problem following this exact format:

{previous_context}

1. Academic Lecture: Generate an academic lecture on any subject (psychology, biology, economics, history, etc.) approximately 200 words. The lecture should present a clear academic concept with examples, explanations, or applications.

2. Question: Create a question asking students to summarize the lecture content with reasons/examples (20-30 words). The question should ask for a summary of the main points and supporting details.

Requirements:
- Lecture must be academic and formal in tone
- Content should be suitable for university-level students
- Include specific examples, explanations, or applications of concepts
- Speaking speed for audio: 2.2-2.4 words per second (approximately 200 words for 90 seconds)
- Question should ask for summary with reasons/examples/details

Return ONLY valid JSON with this exact structure. Do not include any text before or after the JSON:

{{
  "lecture_script": "Write the academic lecture here as one continuous string without line breaks",
  "question": "Write the question here as one continuous string"
}}

CRITICAL JSON REQUIREMENTS:
- Must be valid JSON syntax with proper commas and quotes
- No line breaks within string values
- Use double quotes only
- Include comma after each field except the last
- No additional text outside the JSON object"""
        
        try:
            response = await self.call_gpt4(
                prompt=prompt,
                system_message=system_message,
                temperature=0.3,
                max_tokens=1000
            )
            
            # Clean response to avoid JSON parsing issues
            cleaned_response = response.strip()
            # Remove any potential control characters except newlines, carriage returns, and tabs
            cleaned_response = ''.join(char for char in cleaned_response if ord(char) >= 32 or char in '\n\r\t')
            
            logger.info(f"Task 4 GPT-4 response: {cleaned_response[:200]}...")
            
            # Parse JSON response
            problem_data = json.loads(cleaned_response)
            
            # Validate required fields
            required_fields = ["lecture_script", "question"]
            for field in required_fields:
                if field not in problem_data:
                    raise ProblemGenerationError(f"Missing required field: {field}")
            
            return problem_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse GPT-4 response as JSON: {e}")
            logger.error(f"Raw response: {response}")
            raise ProblemGenerationError("Failed to generate valid problem format")
        except ExternalAPIError:
            raise
        except Exception as e:
            logger.error(f"Task 4 problem generation failed: {e}")
            raise ProblemGenerationError(f"Failed to generate Task 4 problem: {str(e)}")

    async def generate_task2_problem(self, previous_questions: list = None) -> Dict[str, str]:
        """
        Generate TOEFL Task 2 (Integrated Speaking) problem using GPT-4.
        
        Args:
            previous_questions: List of previously generated questions to avoid duplicates
        
        Returns:
            Dictionary with announcement_text, conversation_script, and question
            
        Raises:
            ProblemGenerationError: If problem generation fails
        """
        system_message = """You are an expert TOEFL iBT test creator specializing in Task 2 (Integrated Speaking) questions.
Generate authentic campus-related content that matches official TOEFL standards."""
        
        # Build previous questions context (temporarily disabled for debugging)
        previous_context = ""
        # if previous_questions:
        #     previous_context = f"""
        # IMPORTANT: Avoid generating content similar to these previously used questions:
        # {chr(10).join(f"- {q}" for q in previous_questions[-10:])}
        # 
        # Make sure your new announcement topic and question are distinctly different from previous ones.
        # """

        prompt = f"""Create a TOEFL Speaking Task 2 (Integrated) problem following this exact format:

{previous_context}

1. University Announcement: Generate an official announcement from university administration, dormitory office, library, dining services, or other campus facilities to students (approximately 100 words). This should be a formal notice about policy changes, facility updates, service modifications, schedule changes, or new campus initiatives.

2. Student Conversation: Generate a conversation between two university students who have read the announcement. Each student should express their opinion about the announcement with clear reasons. The conversation should be natural and show different perspectives.

3. Question: Create a question asking students to summarize both students' opinions and their reasons (20-30 words). The question should ask for a summary of what each student thinks and why.

Requirements:
- Announcement must be from university administration or campus facilities (library, dining, housing, etc.)
- Announcement should include specific details about what's changing and why
- Students should have contrasting opinions with clear, logical reasoning
- Conversation should sound like natural campus dialogue between friends/classmates
- Each student should give at least 2 reasons for their opinion
- Question should specifically ask for BOTH students' opinions AND their reasons
- Speaking speed for audio: 2.2-2.4 words per second (approximately 130-150 words for 60 seconds)

Return ONLY valid JSON with this exact structure. Do not include any text before or after the JSON:

{{
  "announcement_text": "Write the formal university announcement here as one continuous string without line breaks",
  "conversation_script": "Write the student conversation here as one continuous string without line breaks", 
  "question": "Write the question here as one continuous string"
}}

CRITICAL JSON REQUIREMENTS:
- Must be valid JSON syntax with proper commas and quotes
- No line breaks within string values
- Use double quotes only
- Include comma after each field except the last
- No additional text outside the JSON object"""
        
        try:
            response = await self.call_gpt4(
                prompt=prompt,
                system_message=system_message,
                temperature=0.3,
                max_tokens=1000
            )
            
            # Clean response to avoid JSON parsing issues
            cleaned_response = response.strip()
            # Remove any potential control characters except newlines, carriage returns, and tabs
            cleaned_response = ''.join(char for char in cleaned_response if ord(char) >= 32 or char in '\n\r\t')
            
            logger.info(f"Task 2 GPT-4 response: {cleaned_response[:200]}...")
            
            # Parse JSON response
            problem_data = json.loads(cleaned_response)
            
            # Validate required fields
            required_fields = ["announcement_text", "conversation_script", "question"]
            for field in required_fields:
                if field not in problem_data:
                    raise ProblemGenerationError(f"Missing required field: {field}")
            
            return problem_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse GPT-4 response as JSON: {e}")
            logger.error(f"Raw response: {response}")
            raise ProblemGenerationError("Failed to generate valid problem format")
        except ExternalAPIError:
            raise
        except Exception as e:
            logger.error(f"Task 2 problem generation failed: {e}")
            raise ProblemGenerationError(f"Failed to generate Task 2 problem: {str(e)}")

    async def generate_task1_question(self, previous_questions: list = None) -> Dict[str, str]:
        """
        Generate TOEFL Task 1 (Independent Speaking) question using GPT-4.
        
        Args:
            previous_questions: List of previously generated questions to avoid duplicates
        
        Returns:
            Dictionary with question text
            
        Raises:
            ProblemGenerationError: If question generation fails
        """
        system_message = """You are an expert TOEFL iBT test creator specializing in Task 1 (Independent Speaking) questions.
Generate authentic questions that match official TOEFL standards and encourage personal responses."""
        
        # Build previous questions context
        previous_context = ""
        if previous_questions:
            previous_context = f"""
IMPORTANT: Avoid generating questions similar to these previously used questions:
{chr(10).join(f"- {q}" for q in previous_questions[-10:])}

Make sure your new question is distinctly different in topic, focus, and wording.
"""

        prompt = f"""Create a TOEFL Speaking Task 1 (Independent) question.

{previous_context}

Requirements:
- 20-30 words in length
- Ask about personal experiences, opinions, or preferences
- Be clear and specific
- Allow for detailed personal response
- Follow official TOEFL Task 1 format
- Must be significantly different from any previously used questions

Examples of good Task 1 questions:
- "Describe a piece of news you have received that made you happy. Why did it make you happy?"
- "Talk about a skill you would like to learn. Explain why this skill would be good for you to have."
- "Describe a place you have never visited but would like to go to someday. Explain why you want to visit this place."

Return ONLY valid JSON with this structure:
{{
  "question": "<your generated question>"
}}"""
        
        try:
            response = await self.call_gpt4(
                prompt=prompt,
                system_message=system_message,
                temperature=0.8,
                max_tokens=200
            )
            
            # Parse JSON response
            question_data = json.loads(response)
            
            # Validate required field
            if "question" not in question_data:
                raise ProblemGenerationError("Missing required field: question")
            
            # Validate question length (approximately 20-30 words)
            question_words = len(question_data["question"].split())
            if question_words < 15 or question_words > 40:
                logger.warning(f"Question length ({question_words} words) outside optimal range")
            
            return question_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse GPT-4 response as JSON: {e}")
            raise ProblemGenerationError("Failed to generate valid question format")
        except ExternalAPIError:
            raise
        except Exception as e:
            logger.error(f"Task 1 question generation failed: {e}")
            raise ProblemGenerationError(f"Failed to generate Task 1 question: {str(e)}")

    async def generate_problem(
        self,
        topic_category: str,
        task_type: str = "task3",
        previous_questions: list = None
    ) -> Dict[str, str]:
        """
        Generate TOEFL Task 3 problem using GPT-4.
        
        Args:
            topic_category: Academic topic (psychology, biology, economics, sociology, etc.)
            task_type: Task type (default: "task3")
            previous_questions: List of previously generated questions to avoid duplicates
            
        Returns:
            Dictionary with reading_text, lecture_script, and question
            
        Raises:
            ProblemGenerationError: If problem generation fails
        """
        system_message = """You are an expert TOEFL iBT test creator specializing in Task 3 (Academic Integrated) questions.
Generate authentic, academic-level content that matches official TOEFL standards."""
        
        # Build previous questions context
        previous_context = ""
        if previous_questions:
            previous_context = f"""
IMPORTANT: Avoid generating content similar to these previously used questions:
{chr(10).join(f"- {q}" for q in previous_questions[-10:])}

Make sure your new concept and question are distinctly different from previous ones.
"""

        prompt = f"""Create a complete TOEFL Speaking Task 3 problem on the topic of {topic_category}.

{previous_context}

Provide the following in JSON format:
1. reading_text: A 75-100 word academic passage introducing a concept (suitable for 45 seconds of reading)
2. lecture_script: A 150-200 word lecture that provides examples or applications of the concept (suitable for 60-90 seconds)
3. question: A clear question asking the student to explain the concept and how the examples relate to it

The content should be:
- Academic and formal in tone
- Clear and well-structured
- Appropriate for advanced English learners
- Focused on a specific concept with concrete examples

Return ONLY valid JSON with these three keys."""
        
        try:
            response = await self.call_gpt4(
                prompt=prompt,
                system_message=system_message,
                temperature=0.8,
                max_tokens=800
            )
            
            # Parse JSON response
            problem_data = json.loads(response)
            
            # Validate required fields
            required_fields = ["reading_text", "lecture_script", "question"]
            for field in required_fields:
                if field not in problem_data:
                    raise ProblemGenerationError(f"Missing required field: {field}")
            
            return problem_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse GPT-4 response as JSON: {e}")
            raise ProblemGenerationError("Failed to generate valid problem format")
        except ExternalAPIError:
            raise
        except Exception as e:
            logger.error(f"Problem generation failed: {e}")
            raise ProblemGenerationError(f"Failed to generate problem: {str(e)}")
    
    async def score_task1_response(
        self,
        transcript: str,
        question: str
    ) -> Dict[str, Any]:
        """
        Score TOEFL Task 1 (Independent Speaking) response using GPT-4.
        
        Args:
            transcript: User's transcribed response
            question: The question asked
            
        Returns:
            Dictionary with scores and feedback
            
        Raises:
            ScoringError: If scoring fails
        """
        system_message = """You are an expert TOEFL iBT Speaking rater trained in official ETS scoring rubrics for Task 1 (Independent Speaking).
Use the official 0-4 scoring scale with these criteria:

0点: 全く話していない
1点: ほとんど話していない
2点: 英語の間違いが散見しつつ、テンポと構成がまずく問に答えきれていない
3点: 英語の間違いは散見しつつも、テンポと構成よく問に答えきれている
4点: 英語の表現がよく、構成も回答もよい"""
        
        prompt = f"""Score this TOEFL Speaking Task 1 response according to official rubrics.

QUESTION:
{question}

STUDENT RESPONSE:
{transcript}

Evaluate based on:
1. Delivery: Fluency, pronunciation, pacing, clarity
2. Language Use: Grammar, vocabulary, sentence structure
3. Topic Development: Content relevance, detail, organization, coherence

Provide an overall score (0-4) based on the Japanese criteria provided in the system message.

Return ONLY valid JSON with this structure:
{{
  "overall_score": <0-4>,
  "delivery_feedback": "<detailed feedback on fluency, pronunciation, pacing>",
  "language_use_feedback": "<detailed feedback on grammar, vocabulary>",
  "topic_dev_feedback": "<detailed feedback on content and organization>",
  "improvement_tips": ["<tip1>", "<tip2>", "<tip3>"],
  "strengths": ["<strength1>", "<strength2>"]
}}"""
        
        try:
            response = await self.call_gpt4(
                prompt=prompt,
                system_message=system_message,
                temperature=0.3,
                max_tokens=800
            )
            
            # Parse JSON response
            scoring_data = json.loads(response)
            
            # Validate overall score
            if "overall_score" not in scoring_data:
                raise ScoringError("Missing required field: overall_score")
            
            score = scoring_data["overall_score"]
            if not isinstance(score, (int, float)) or score < 0 or score > 4:
                raise ScoringError(f"Invalid overall score: {score}")
            
            return scoring_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Task 1 scoring response as JSON: {e}")
            raise ScoringError("Failed to generate valid scoring format")
        except ExternalAPIError:
            raise
        except Exception as e:
            logger.error(f"Task 1 scoring failed: {e}")
            raise ScoringError(f"Failed to score Task 1 response: {str(e)}")

    async def score_response(
        self,
        transcript: str,
        reading_text: Optional[str],
        lecture_script: str,
        question: str
    ) -> Dict[str, Any]:
        """
        Score TOEFL speaking response using GPT-4.
        Handles both Task 3 (with reading passage) and Task 4 (lecture only).
        
        Args:
            transcript: User's transcribed response
            reading_text: Original reading passage (None for Task 4)
            lecture_script: Original lecture script
            question: The question asked
            
        Returns:
            Dictionary with scores and feedback
            
        Raises:
            ScoringError: If scoring fails
        """
        system_message = """You are an expert TOEFL iBT Speaking rater trained in official ETS scoring rubrics.
You evaluate both Task 3 (Reading + Lecture) and Task 4 (Lecture only) responses.
Use the official Japanese scoring criteria for TOEFL Speaking:

0点: 全く話していない
1点: ほとんど話していない
2点: 英語の間違いが散見しつつ、テンポと構成がまずく問に答えきれていない
3点: 英語の間違いは散見しつつも、テンポと構成よく問に答えきれている
4点: 英語の表現がよく、構成も回答もよい

Evaluate responses based on three criteria: Delivery, Language Use, and Topic Development.
Each criterion is scored on a 0-4 scale, and provide an overall score based on the criteria above."""
        
        # Determine task type based on whether reading_text is provided
        task_type = "Task 3" if reading_text else "Task 4"
        
        # Build prompt with conditional reading passage
        reading_section = f"""READING PASSAGE:
{reading_text}

""" if reading_text else ""
        
        prompt = f"""Score this TOEFL Speaking {task_type} response according to the official Japanese scoring criteria.

{reading_section}LECTURE:
{lecture_script}

QUESTION:
{question}

STUDENT RESPONSE:
{transcript}

Apply the official Japanese TOEFL scoring criteria:
0点: 全く話していない (Not speaking at all)
1点: ほとんど話していない (Barely speaking)
2点: 英語の間違いが散見しつつ、テンポと構成がまずく問に答えきれていない (Many English errors, poor tempo and structure, unable to fully answer the question)
3点: 英語の間違いは散見しつつも、テンポと構成よく問に答えきれている (Some English errors but good tempo and structure, able to answer the question well)
4点: 英語の表現がよく、構成も回答もよい (Good English expression, good structure and response)

Provide detailed scores (0-4) and feedback for:
1. Delivery: Clarity, fluency, pronunciation, pacing
2. Language Use: Grammar, vocabulary, sentence structure
3. Topic Development: Content accuracy, completeness, coherence

The overall score should reflect the holistic assessment based on the Japanese criteria above.

Return ONLY valid JSON with this structure:
{{
  "delivery_score": <0-4>,
  "delivery_feedback": "<detailed feedback in Japanese>",
  "language_use_score": <0-4>,
  "language_use_feedback": "<detailed feedback in Japanese>",
  "topic_dev_score": <0-4>,
  "topic_dev_feedback": "<detailed feedback in Japanese>",
  "overall_score": <0-4>,
  "improvement_tips": ["<tip1 in Japanese>", "<tip2 in Japanese>", "<tip3 in Japanese>"]
}}"""
        
        try:
            response = await self.call_gpt4(
                prompt=prompt,
                system_message=system_message,
                temperature=0.3,
                max_tokens=1000
            )
            
            # Parse JSON response
            scoring_data = json.loads(response)
            
            # Validate scores are in range
            score_fields = ["delivery_score", "language_use_score", "topic_dev_score", "overall_score"]
            for field in score_fields:
                if field not in scoring_data:
                    raise ScoringError(f"Missing required field: {field}")
                score = scoring_data[field]
                if not isinstance(score, (int, float)) or score < 0 or score > 4:
                    raise ScoringError(f"Invalid score for {field}: {score}")
            
            return scoring_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse scoring response as JSON: {e}")
            raise ScoringError("Failed to generate valid scoring format")
        except ExternalAPIError:
            raise
        except Exception as e:
            logger.error(f"Scoring failed: {e}")
            raise ScoringError(f"Failed to score response: {str(e)}")
    
    async def generate_task1_model_answer(
        self,
        question: str
    ) -> Dict[str, Any]:
        """
        Generate model answer for TOEFL Task 1 using GPT-4.
        
        Args:
            question: The question asked
            
        Returns:
            Dictionary with model_answer and highlighted_phrases
            
        Raises:
            ExternalAPIError: If generation fails
        """
        system_message = """You are an expert TOEFL Speaking instructor who creates exemplary model answers for Task 1 (Independent Speaking).
Generate high-scoring responses that demonstrate excellent structure, fluency, and personal detail."""
        
        prompt = f"""Create a model answer for this TOEFL Speaking Task 1 question.

QUESTION:
{question}

Generate:
1. A complete, well-structured model answer (45 seconds speaking time, ~130-150 words)
2. Include personal details and specific examples
3. Use clear organization with introduction, main points, and conclusion
4. Identify key phrases that demonstrate good structure and transitions

Return ONLY valid JSON with this structure:
{{
  "model_answer": "<complete answer text>",
  "highlighted_phrases": [
    {{
      "text": "<phrase>",
      "category": "<introduction|transition|example|conclusion>",
      "explanation": "<why this phrase is effective>"
    }}
  ]
}}"""
        
        try:
            response = await self.call_gpt4(
                prompt=prompt,
                system_message=system_message,
                temperature=0.7,
                max_tokens=600
            )
            
            # Parse JSON response
            model_data = json.loads(response)
            
            # Validate required fields
            if "model_answer" not in model_data:
                raise ExternalAPIError("OpenAI", "Missing model_answer in response")
            if "highlighted_phrases" not in model_data:
                model_data["highlighted_phrases"] = []
            
            return model_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Task 1 model answer response as JSON: {e}")
            raise ExternalAPIError("OpenAI", "Failed to generate valid model answer format")
        except ExternalAPIError:
            raise
        except Exception as e:
            logger.error(f"Task 1 model answer generation failed: {e}")
            raise ExternalAPIError("OpenAI", f"Failed to generate Task 1 model answer: {str(e)}")

    async def generate_task2_model_answer(
        self,
        announcement_text: str,
        conversation_script: str,
        question: str
    ) -> Dict[str, Any]:
        """
        Generate model answer for TOEFL Task 2 using GPT-4.
        
        Args:
            announcement_text: University announcement text
            conversation_script: Student conversation script
            question: The question asked
            
        Returns:
            Dictionary with model_answer and highlighted_phrases
            
        Raises:
            ExternalAPIError: If generation fails
        """
        system_message = """You are an expert TOEFL Speaking instructor who creates exemplary model answers for Task 2 (Integrated Speaking).
Generate high-scoring responses that demonstrate excellent structure and accurate summarization."""
        
        prompt = f"""Create a model answer for this TOEFL Speaking Task 2 question.

UNIVERSITY ANNOUNCEMENT:
{announcement_text}

STUDENT CONVERSATION:
{conversation_script}

QUESTION:
{question}

Generate:
1. A complete, well-structured model answer (60 seconds speaking time, ~150-180 words)
2. Accurately summarize the students' opinions and reasons
3. Use clear organization and appropriate transitions
4. Identify key phrases that demonstrate good structure (transitions, summaries, conclusions)

Return ONLY valid JSON with this structure:
{{
  "model_answer": "<complete answer text>",
  "highlighted_phrases": [
    {{
      "text": "<phrase>",
      "category": "<transition|summary|conclusion>",
      "useful_for_writing": <true|false>
    }}
  ]
}}"""
        
        try:
            response = await self.call_gpt4(
                prompt=prompt,
                system_message=system_message,
                temperature=0.7,
                max_tokens=800
            )
            
            # Parse JSON response
            model_data = json.loads(response)
            
            # Validate required fields
            if "model_answer" not in model_data:
                raise ExternalAPIError("OpenAI", "Missing model_answer in response")
            if "highlighted_phrases" not in model_data:
                model_data["highlighted_phrases"] = []
            
            return model_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Task 2 model answer response as JSON: {e}")
            raise ExternalAPIError("OpenAI", "Failed to generate valid model answer format")
        except ExternalAPIError:
            raise
        except Exception as e:
            logger.error(f"Task 2 model answer generation failed: {e}")
            raise ExternalAPIError("OpenAI", f"Failed to generate Task 2 model answer: {str(e)}")

    async def generate_model_answer(
        self,
        reading_text: Optional[str],
        lecture_script: str,
        question: str
    ) -> Dict[str, Any]:
        """
        Generate model answer for TOEFL Task 3 or Task 4 using GPT-4.
        
        Args:
            reading_text: Original reading passage (None for Task 4)
            lecture_script: Original lecture script
            question: The question asked
            
        Returns:
            Dictionary with model_answer and highlighted_phrases
            
        Raises:
            ExternalAPIError: If generation fails
        """
        system_message = """You are an expert TOEFL Speaking instructor who creates exemplary model answers.
Generate high-scoring responses that demonstrate excellent structure and language use."""
        
        # Determine task type and build prompt accordingly
        task_type = "Task 3" if reading_text else "Task 4"
        
        # Build prompt with conditional reading passage
        reading_section = f"""READING PASSAGE:
{reading_text}

""" if reading_text else ""
        
        prompt = f"""Create a model answer for this TOEFL Speaking {task_type} question.

{reading_section}LECTURE:
{lecture_script}

QUESTION:
{question}

Generate:
1. A complete, well-structured model answer (60 seconds speaking time, ~150-180 words)
2. Identify key phrases that demonstrate good structure (transitions, examples, conclusions)
3. Mark phrases that are also useful for TOEFL Writing

Return ONLY valid JSON with this structure:
{{
  "model_answer": "<complete answer text>",
  "highlighted_phrases": [
    {{
      "text": "<phrase>",
      "category": "<transition|example|conclusion>",
      "useful_for_writing": <true|false>
    }}
  ]
}}"""
        
        try:
            response = await self.call_gpt4(
                prompt=prompt,
                system_message=system_message,
                temperature=0.7,
                max_tokens=800
            )
            
            # Parse JSON response
            model_data = json.loads(response)
            
            # Validate required fields
            if "model_answer" not in model_data:
                raise ExternalAPIError("OpenAI", "Missing model_answer in response")
            if "highlighted_phrases" not in model_data:
                model_data["highlighted_phrases"] = []
            
            return model_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse model answer response as JSON: {e}")
            raise ExternalAPIError("OpenAI", "Failed to generate valid model answer format")
        except ExternalAPIError:
            raise
        except Exception as e:
            logger.error(f"Model answer generation failed: {e}")
            raise ExternalAPIError("OpenAI", f"Failed to generate model answer: {str(e)}")


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
            ExternalAPIError: If generation fails
        """
        system_message = """あなたはTOEFL iBT Speakingの専門講師です。学習者の回答を詳細に分析し、個別化されたフィードバックを日本語で提供してください。

以下の観点から評価してください：
1. 良い点（具体的に何ができているかを日本語で）
2. 改善点（具体的に何を改善すべきかを日本語で）
3. 具体的な改善案（学習者の回答を踏まえた個別のアドバイスを日本語で）
4. スコアアップのコツ（問題の内容も考慮した実践的なアドバイスを日本語で）
5. 改善版英語回答（学習者の回答を基にした改善版を英語で）

**重要な指示**:
- フィードバック部分（strengths、improvements、specific_suggestions、score_improvement_tips）は必ず日本語で記述してください
- 改善版回答（improved_response）のみ英語で記述してください
- フィードバックは建設的で、学習者のモチベーションを高める内容にしてください
- 学習者の実際の発言を引用して、具体的で実践的なアドバイスを提供してください"""
        
        # Build context based on task type
        context_sections = []
        
        if task_type == "task1":
            context_sections.append(f"質問: {question}")
        elif task_type == "task2":
            if announcement_text:
                context_sections.append(f"大学からのお知らせ: {announcement_text}")
            if conversation_script:
                context_sections.append(f"学生の会話: {conversation_script}")
            context_sections.append(f"質問: {question}")
        elif task_type == "task3":
            if reading_text:
                context_sections.append(f"リーディング: {reading_text}")
            if lecture_script:
                context_sections.append(f"講義: {lecture_script}")
            context_sections.append(f"質問: {question}")
        elif task_type == "task4":
            if lecture_script:
                context_sections.append(f"講義: {lecture_script}")
            context_sections.append(f"質問: {question}")
        
        context = "\n\n".join(context_sections)
        
        prompt = f"""以下のTOEFL Speaking {task_type.upper()}の問題に対する学習者の回答を分析し、個別化されたフィードバックを日本語で提供してください。

【問題内容】
{context}

【学習者の回答】
{user_transcript}

【分析要求】
1. この学習者の回答の良い点を具体的に日本語で指摘してください
2. 改善が必要な点を具体的に日本語で指摘してください
3. この学習者の回答内容を踏まえた具体的な改善案を日本語で提示してください
4. この問題の内容を考慮したスコアアップのコツを日本語で提供してください
5. 学習者の回答を基にした改善版の英語回答を作成してください

**重要**: strengths、improvements、specific_suggestions、score_improvement_tipsは必ず日本語で記述してください。improved_responseのみ英語で記述してください。

以下のJSON形式で回答してください：

{{
  "strengths": ["良い点1（日本語）", "良い点2（日本語）", "良い点3（日本語）"],
  "improvements": ["改善点1（日本語）", "改善点2（日本語）", "改善点3（日本語）"],
  "specific_suggestions": "この学習者の回答を踏まえた具体的な改善案を日本語でここに詳しく記述してください。学習者が実際に言った内容を引用しながら、どのように改善できるかを具体的に日本語で説明してください。",
  "score_improvement_tips": "この問題の内容と学習者の回答レベルを考慮した、実践的なスコアアップのコツを日本語でここに記述してください。次回同様の問題に取り組む際の具体的なアドバイスを日本語で含めてください。",
  "improved_response": "学習者の回答を基に、より高いスコアが期待できる改善版の英語回答をここに英語で記述してください。学習者の良い部分は残しつつ、文法、語彙、構成、内容を改善した完全な英語回答を提供してください。45-60秒で話せる長さ（約130-180語）の英語にしてください。"
}}"""
        
        try:
            response = await self.call_gpt4(
                prompt=prompt,
                system_message=system_message,
                temperature=0.7,
                max_tokens=1200
            )
            
            # Parse JSON response
            review_data = json.loads(response)
            
            # Validate required fields
            required_fields = ["strengths", "improvements", "specific_suggestions", "score_improvement_tips", "improved_response"]
            for field in required_fields:
                if field not in review_data:
                    raise ExternalAPIError("OpenAI", f"Missing required field: {field}")
            
            # Ensure strengths and improvements are lists
            if not isinstance(review_data["strengths"], list):
                review_data["strengths"] = [review_data["strengths"]]
            if not isinstance(review_data["improvements"], list):
                review_data["improvements"] = [review_data["improvements"]]
            
            return review_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI review response as JSON: {e}")
            raise ExternalAPIError("OpenAI", "Failed to generate valid AI review format")
        except ExternalAPIError:
            raise
        except Exception as e:
            logger.error(f"AI review generation failed: {e}")
            raise ExternalAPIError("OpenAI", f"Failed to generate AI review: {str(e)}")


# Singleton instance
_openai_client: Optional[OpenAIClient] = None


def get_openai_client() -> OpenAIClient:
    """
    Get or create singleton OpenAI client instance.
    
    Returns:
        OpenAI client instance
    """
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAIClient()
    return _openai_client
