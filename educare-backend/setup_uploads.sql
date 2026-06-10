-- File uploads: peer attachments + quiz question images

CREATE TABLE IF NOT EXISTS peer_attachments (
    attachment_id   INT AUTO_INCREMENT PRIMARY KEY,
    parent_type     ENUM('question', 'answer') NOT NULL,
    parent_id       INT NOT NULL,
    file_url        VARCHAR(512) NOT NULL,
    file_name       VARCHAR(255) NOT NULL,
    content_type    VARCHAR(128) DEFAULT '',
    is_image        TINYINT(1) DEFAULT 0,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_peer_att_parent (parent_type, parent_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

ALTER TABLE quiz_questions
    ADD COLUMN IF NOT EXISTS question_image VARCHAR(512) NULL AFTER question_text;
