-- EDUCARE Auth Enhancements: Profile + OTP Password Reset
-- Run this once in your educare MySQL DB

-- 1. Add profile_picture to users
SET @col_pic := 0;
SELECT COUNT(*) INTO @col_pic
  FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = 'educare'
    AND TABLE_NAME   = 'users'
    AND COLUMN_NAME  = 'profile_picture';
SET @sql_pic := IF(@col_pic = 0,
  'ALTER TABLE users ADD COLUMN profile_picture VARCHAR(512) NULL AFTER email',
  'SELECT "profile_picture column exists" AS status');
PREPARE stmt_pic FROM @sql_pic;
EXECUTE stmt_pic;
DEALLOCATE PREPARE stmt_pic;

-- 2. Create password_resets table for OTP flow (6-digit, 10min, 3 attempts)
CREATE TABLE IF NOT EXISTS password_resets (
    reset_id      INT AUTO_INCREMENT PRIMARY KEY,
    email         VARCHAR(255) NOT NULL,
    otp           VARCHAR(6) NOT NULL,
    expires_at    DATETIME NOT NULL,
    attempts      INT DEFAULT 0,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_expiry (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Optional cleanup old resets (can run periodically)
-- DELETE FROM password_resets WHERE expires_at < NOW();

SELECT 'Auth schema (profile + password_resets) ready' AS status;
