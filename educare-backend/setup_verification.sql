-- Add email verification columns to users table
-- Run this script in MySQL to add verification columns

-- Check if columns exist before adding
SET @column_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = 'educare' 
    AND TABLE_NAME = 'users' 
    AND COLUMN_NAME = 'is_verified'
);

-- Add columns if they don't exist
ALTER TABLE users 
ADD COLUMN is_verified BOOLEAN DEFAULT FALSE AFTER role,
ADD COLUMN verification_token VARCHAR(255) NULL,
ADD COLUMN token_expiry DATETIME NULL;

-- Add index for faster token lookup
CREATE INDEX idx_verification_token ON users(verification_token);

-- Add unique constraint for token (nullable values excluded)
ALTER TABLE users MODIFY verification_token VARCHAR(255) NULL;

SELECT 'Verification columns added successfully' AS status;