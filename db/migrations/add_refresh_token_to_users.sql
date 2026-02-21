-- Migration: Add refresh_token column to users table
-- Date: 2026-02-03
-- Description: Adds refresh_token column to users table to support JWT refresh tokens

-- Add refresh_token column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'users' 
        AND column_name = 'refresh_token'
    ) THEN
        ALTER TABLE users ADD COLUMN refresh_token TEXT;
        RAISE NOTICE 'Column refresh_token added to users table';
    ELSE
        RAISE NOTICE 'Column refresh_token already exists in users table';
    END IF;
END $$;
