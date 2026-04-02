-- SQL Script to create a family user and link to students
-- Run this script in your MySQL database

-- Step 1: Check existing users
SELECT user_id, full_name, email, role FROM users;

-- Step 2: Check existing students
SELECT s.user_id, u.full_name, s.grade_level, s.section 
FROM students s 
JOIN users u ON s.user_id = u.user_id;

-- Step 3: Create a family user (adjust values as needed)
INSERT INTO users (full_name, email, password, role) 
VALUES ('John Parent', 'parent@educare.com', 'password123', 'family');

-- Step 4: Get the user_id of the newly created family user
-- Note: Replace @family_user_id with the actual ID from Step 3
-- You can get it by running: SELECT LAST_INSERT_ID();

-- Step 5: Link the family user to students
-- Replace @family_user_id with the actual user_id from Step 4
-- Replace student_id values with actual student user_ids from Step 2

-- Example: Link to student with user_id = 1
INSERT INTO family (user_id, student_id, relationship) 
VALUES (LAST_INSERT_ID(), 1, 'parent');

-- Example: Link to multiple students
-- INSERT INTO family (user_id, student_id, relationship) 
-- VALUES 
--   (LAST_INSERT_ID(), 1, 'parent'),
--   (LAST_INSERT_ID(), 2, 'parent');

-- Step 6: Verify the setup
SELECT 
    u.user_id,
    u.full_name as parent_name,
    u.email as parent_email,
    f.relationship,
    s.user_id as student_id,
    su.full_name as student_name,
    s.grade_level,
    s.section
FROM users u
JOIN family f ON u.user_id = f.user_id
JOIN students s ON f.student_id = s.user_id
JOIN users su ON s.user_id = su.user_id
WHERE u.role = 'family';

-- Step 7: Test login credentials
-- Email: parent@educare.com
-- Password: password123
