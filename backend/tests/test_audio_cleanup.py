"""
Tests for audio file cleanup utilities.
"""
import pytest
import os
import tempfile
from pathlib import Path
from utils.audio_cleanup import cleanup_audio_file, schedule_audio_cleanup, cleanup_old_audio_files


@pytest.fixture
def temp_audio_dir():
    """Create a temporary directory for audio files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_audio_file(temp_audio_dir):
    """Create a sample audio file for testing."""
    file_path = Path(temp_audio_dir) / "test_audio.mp3"
    file_path.write_text("fake audio content")
    return str(file_path)


def test_cleanup_audio_file_success(sample_audio_file):
    """Test successful audio file deletion."""
    # Verify file exists
    assert os.path.exists(sample_audio_file)
    
    # Clean up file
    result = cleanup_audio_file(sample_audio_file)
    
    # Verify deletion
    assert result is True
    assert not os.path.exists(sample_audio_file)


def test_cleanup_audio_file_nonexistent():
    """Test cleanup of non-existent file."""
    result = cleanup_audio_file("/nonexistent/path/audio.mp3")
    
    # Should return True (file is gone, which is the goal)
    assert result is True


def test_cleanup_audio_file_empty_path():
    """Test cleanup with empty path."""
    result = cleanup_audio_file("")
    assert result is False


def test_cleanup_audio_file_directory(temp_audio_dir):
    """Test cleanup fails when path is a directory."""
    result = cleanup_audio_file(temp_audio_dir)
    assert result is False


def test_schedule_audio_cleanup_success(temp_audio_dir):
    """Test scheduling cleanup for a session."""
    # Create a lecture audio file
    session_id = "test-session-123"
    audio_file = Path(temp_audio_dir) / f"lecture_{session_id}.mp3"
    audio_file.write_text("fake lecture audio")
    
    # Verify file exists
    assert audio_file.exists()
    
    # Schedule cleanup
    result = schedule_audio_cleanup(session_id, temp_audio_dir)
    
    # Verify deletion
    assert result is True
    assert not audio_file.exists()


def test_schedule_audio_cleanup_no_file(temp_audio_dir):
    """Test scheduling cleanup when no file exists."""
    session_id = "nonexistent-session"
    
    # Should succeed (no file to clean up)
    result = schedule_audio_cleanup(session_id, temp_audio_dir)
    assert result is True


def test_cleanup_old_audio_files(temp_audio_dir):
    """Test cleanup of old audio files."""
    import time
    
    # Create some audio files
    old_file = Path(temp_audio_dir) / "lecture_old.mp3"
    old_file.write_text("old audio")
    
    # Make the file appear old by modifying its timestamp
    old_time = time.time() - (25 * 3600)  # 25 hours ago
    os.utime(old_file, (old_time, old_time))
    
    # Create a recent file
    new_file = Path(temp_audio_dir) / "lecture_new.mp3"
    new_file.write_text("new audio")
    
    # Run cleanup (max age 24 hours)
    deleted_count = cleanup_old_audio_files(temp_audio_dir, max_age_hours=24)
    
    # Old file should be deleted, new file should remain
    assert deleted_count == 1
    assert not old_file.exists()
    assert new_file.exists()


def test_cleanup_old_audio_files_empty_directory(temp_audio_dir):
    """Test cleanup with no audio files."""
    deleted_count = cleanup_old_audio_files(temp_audio_dir, max_age_hours=24)
    assert deleted_count == 0


def test_cleanup_old_audio_files_nonexistent_directory():
    """Test cleanup with non-existent directory."""
    deleted_count = cleanup_old_audio_files("/nonexistent/directory", max_age_hours=24)
    assert deleted_count == 0
