-- Assistant conversations table for chatbot history
CREATE TABLE IF NOT EXISTS assistant_conversations (
    conversation_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    user_message TEXT NOT NULL,
    ai_response TEXT NOT NULL,
    source_citation VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE
);

-- Index for faster lookups by student_id
CREATE INDEX IF NOT EXISTS idx_assistant_conversations_student_id ON assistant_conversations(student_id);