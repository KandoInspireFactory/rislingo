"""
Audio file cleanup utilities for TOEFL Speaking Master API.
Handles automatic deletion of audio files after scoring.
"""
import os
import logging
from pathlib import Path
from typing import Optional


logger = logging.getLogger(__name__)


def cleanup_audio_file(file_path: str) -> bool:
    """
    Delete an audio file from the filesystem.
    
    This function is called after scoring is complete to ensure
    audio data is not retained longer than necessary (privacy/security).
    
    Args:
        file_path: Path to the audio file to delete
        
    Returns:
        True if file was deleted successfully, False otherwise
    """
    try:
        if not file_path:
            logger.warning("cleanup_audio_file called with empty file_path")
            return False
        
        # Convert to Path object for safer handling
        path = Path(file_path)
        
        # Check if file exists
        if not path.exists():
            logger.info(f"Audio file does not exist (already deleted?): {file_path}")
            return True  # Consider this success - file is gone
        
        # Check if it's actually a file (not a directory)
        if not path.is_file():
            logger.warning(f"Path is not a file: {file_path}")
            return False
        
        # Delete the file
        path.unlink()
        logger.info(f"Successfully deleted audio file: {file_path}")
        return True
        
    except PermissionError as e:
        logger.error(f"Permission denied when deleting audio file {file_path}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error deleting audio file {file_path}: {e}")
        return False


def schedule_audio_cleanup(session_id: str, audio_storage_path: Optional[str] = None) -> bool:
    """
    Schedule cleanup of all audio files associated with a practice session.
    
    This function should be called after scoring is complete.
    It deletes the lecture audio file associated with the session.
    
    Args:
        session_id: UUID of the practice session
        audio_storage_path: Base path where audio files are stored
        
    Returns:
        True if cleanup was successful, False otherwise
    """
    try:
        # Get audio storage path from environment or use default
        if audio_storage_path is None:
            audio_storage_path = os.getenv("AUDIO_STORAGE_PATH", "backend/audio_files")
        
        # Construct the expected audio file path
        # Audio files are typically named: lecture_{session_id}.mp3
        audio_file = Path(audio_storage_path) / f"lecture_{session_id}.mp3"
        
        # Try to delete the file
        if audio_file.exists():
            success = cleanup_audio_file(str(audio_file))
            if success:
                logger.info(f"Cleaned up audio for session: {session_id}")
            return success
        else:
            logger.info(f"No audio file found for session: {session_id}")
            return True  # No file to clean up is considered success
            
    except Exception as e:
        logger.error(f"Error scheduling audio cleanup for session {session_id}: {e}")
        return False


def cleanup_old_audio_files(audio_storage_path: Optional[str] = None, max_age_hours: int = 24) -> int:
    """
    Clean up audio files older than specified age.
    
    This is a maintenance function that can be run periodically
    to ensure no orphaned audio files remain.
    
    Args:
        audio_storage_path: Base path where audio files are stored
        max_age_hours: Maximum age in hours before deletion
        
    Returns:
        Number of files deleted
    """
    try:
        import time
        
        # Get audio storage path
        if audio_storage_path is None:
            audio_storage_path = os.getenv("AUDIO_STORAGE_PATH", "backend/audio_files")
        
        storage_path = Path(audio_storage_path)
        
        if not storage_path.exists():
            logger.warning(f"Audio storage path does not exist: {audio_storage_path}")
            return 0
        
        # Calculate cutoff time
        cutoff_time = time.time() - (max_age_hours * 3600)
        deleted_count = 0
        
        # Iterate through audio files
        for audio_file in storage_path.glob("lecture_*.mp3"):
            try:
                # Check file age
                file_mtime = audio_file.stat().st_mtime
                
                if file_mtime < cutoff_time:
                    # File is older than max age, delete it
                    if cleanup_audio_file(str(audio_file)):
                        deleted_count += 1
                        logger.info(f"Deleted old audio file: {audio_file.name}")
                        
            except Exception as e:
                logger.error(f"Error checking/deleting file {audio_file}: {e}")
                continue
        
        logger.info(f"Cleanup complete: deleted {deleted_count} old audio files")
        return deleted_count
        
    except Exception as e:
        logger.error(f"Error in cleanup_old_audio_files: {e}")
        return 0
