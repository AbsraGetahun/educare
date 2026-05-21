-- setup_verification.sql — idempotent
SET @col_verified := 0;
SELECT COUNT(*) INTO @col_verified
  FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = 'educare'
    AND TABLE_NAME   = 'users'
    AND COLUMN_NAME  = 'is_verified';

SET @sql := IF(@col_verified = 0,
  'ALTER TABLE users ADD COLUMN is_verified BOOLEAN DEFAULT FALSE, ADD COLUMN verification_token VARCHAR(255), ADD COLUMN token_expiry DATETIME',
  'SELECT \'skip: columns already exist\' AS status');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @idx_exists := 0;
SELECT COUNT(*) INTO @idx_exists
  FROM INFORMATION_SCHEMA.STATISTICS
  WHERE TABLE_SCHEMA = 'educare'
    AND TABLE_NAME   = 'users'
    AND INDEX_NAME   = 'idx_verification_token';

SET @sql2 := IF(@idx_exists = 0,
  'CREATE INDEX idx_verification_token ON users(verification_token)',
  'SELECT \'skip: index already exists\' AS status');
PREPARE stmt2 FROM @sql2;
EXECUTE stmt2;
DEALLOCATE PREPARE stmt2;

SELECT 'Verification setup complete' AS status;
