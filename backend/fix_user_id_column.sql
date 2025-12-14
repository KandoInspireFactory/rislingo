-- Fix user_id column to allow NULL values
-- This allows practice sessions to be created without a user_id

ALTER TABLE practice_sessions 
ALTER COLUMN user_id DROP NOT NULL;

-- Verify the change
\d practice_sessions

