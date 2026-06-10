-- Peer-to-peer student math questions
-- Questions visible to all students; answers visible only to the asker.

CREATE TABLE IF NOT EXISTS peer_questions (
    question_id   INT AUTO_INCREMENT PRIMARY KEY,
    asker_user_id INT NOT NULL,
    question_text TEXT NOT NULL,
    status        ENUM('open', 'closed') DEFAULT 'open',
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (asker_user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_peer_q_created (created_at DESC),
    INDEX idx_peer_q_asker (asker_user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS peer_answers (
    answer_id         INT AUTO_INCREMENT PRIMARY KEY,
    question_id       INT NOT NULL,
    responder_user_id INT NOT NULL,
    answer_text       TEXT NOT NULL,
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (question_id) REFERENCES peer_questions(question_id) ON DELETE CASCADE,
    FOREIGN KEY (responder_user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    UNIQUE KEY uniq_peer_answer (question_id, responder_user_id),
    INDEX idx_peer_a_question (question_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
