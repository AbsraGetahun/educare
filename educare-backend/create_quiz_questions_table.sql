-- Create quiz_questions table for storing custom quiz questions
-- Run this in MySQL: mysql -u root -p educare < create_quiz_questions_table.sql

CREATE TABLE IF NOT EXISTS quiz_questions (
    question_id INT PRIMARY KEY AUTO_INCREMENT,
    quiz_id INT NOT NULL,
    question_text TEXT NOT NULL,
    option_a VARCHAR(500) NOT NULL,
    option_b VARCHAR(500) NOT NULL,
    option_c VARCHAR(500) DEFAULT NULL,
    option_d VARCHAR(500) DEFAULT NULL,
    correct_answer CHAR(1) NOT NULL DEFAULT 'A',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for faster queries
CREATE INDEX idx_quiz_id ON quiz_questions(quiz_id);

-- Verify table created
SHOW TABLES LIKE 'quiz_questions';
DESCRIBE quiz_questions;