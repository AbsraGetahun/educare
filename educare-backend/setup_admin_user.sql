-- SQL Script to add sample admin user to EDUCARE database
-- Run this script in MySQL to create an admin user

-- First, check if admin user already exists
SELECT 'Checking for existing admin user...' AS status;

-- Insert admin user into users table (if not exists)
INSERT INTO users (full_name, email, password, role, created_at)
SELECT 'System Administrator', 'admin@educare.com', 'admin123', 'admin', NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM users WHERE email = 'admin@educare.com'
);

-- Get the user_id of the admin user
SET @admin_user_id = (SELECT user_id FROM users WHERE email = 'admin@educare.com');

-- Insert into administrator table (if not exists)
INSERT INTO administrator (user_id)
SELECT @admin_user_id
WHERE NOT EXISTS (
    SELECT 1 FROM administrator WHERE user_id = @admin_user_id
);

-- Verify the admin user was created
SELECT 
    u.user_id,
    u.full_name,
    u.email,
    u.role,
    a.admin_id
FROM users u
LEFT JOIN administrator a ON u.user_id = a.user_id
WHERE u.email = 'admin@educare.com';

SELECT 'Admin user setup complete!' AS status;
