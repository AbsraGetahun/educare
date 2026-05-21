-- ============================================================
-- EDUCARE: Extended Schema Migration
-- Creates new tables required for advanced features:
--   generation_history, assistant_conversations,
--   material_ratings, quiz_ai_generations, teacher_settings
-- Also upgrades the `material` table with extra aggregate columns.
-- ============================================================

-- ─── Upgrade material table: add new aggregate columns ───────────
ALTER TABLE material ADD COLUMN IF NOT EXISTS helpful_count INT DEFAULT 0;
ALTER TABLE material ADD COLUMN IF NOT EXISTS not_helpful_count INT DEFAULT 0;

-- ─── Generation history ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS generation_history (
    history_id    INT AUTO_INCREMENT PRIMARY KEY,
    teacher_id    INT            NOT NULL,
    student_id    INT            NOT NULL,
    topic_name    VARCHAR(255)   NOT NULL,
    grade_level   INT            NOT NULL,
    difficulty    ENUM('easy','medium','hard') DEFAULT 'medium',
    generated_at  TIMESTAMP      DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (teacher_id) REFERENCES teachers(user_id)    ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES students(user_id)    ON DELETE CASCADE,
    INDEX idx_teacher_gen   (teacher_id, generated_at DESC),
    INDEX idx_student_topic (student_id, topic_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─── AI assistant conversations ──────────────────────────────────
CREATE TABLE IF NOT EXISTS assistant_conversations (
    conversation_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id      INT    NOT NULL,
    user_message    TEXT   NOT NULL,
    ai_response     TEXT   NOT NULL,
    source_citation VARCHAR(500),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(user_id) ON DELETE CASCADE,
    INDEX idx_student_conv (student_id, created_at DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─── Material quality ratings ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS material_ratings (
    rating_id    INT AUTO_INCREMENT PRIMARY KEY,
    material_id  INT NOT NULL,
    student_id   INT NOT NULL,
    rating       ENUM('helpful','not_helpful') NOT NULL,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (material_id) REFERENCES material(material_id) ON DELETE CASCADE,
    FOREIGN KEY (student_id)  REFERENCES students(user_id)    ON DELETE CASCADE,
    UNIQUE KEY uniq_rating (material_id, student_id),
    INDEX idx_material (material_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─── AI-generated quiz registry ──────────────────────────────────
CREATE TABLE IF NOT EXISTS quiz_ai_generations (
    generation_id INT AUTO_INCREMENT PRIMARY KEY,
    quiz_id       INT            NOT NULL,
    topic         VARCHAR(255)   NOT NULL,
    grade_level   INT            NOT NULL,
    num_questions INT            NOT NULL,
    difficulty    ENUM('easy','medium','hard') DEFAULT 'medium',
    generated_at  TIMESTAMP      DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (quiz_id) REFERENCES quizzes(quiz_id) ON DELETE CASCADE,
    INDEX idx_grade_topic (grade_level, topic, generated_at DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─── Teacher auto-generation settings ────────────────────────────
CREATE TABLE IF NOT EXISTS teacher_settings (
    setting_id       INT AUTO_INCREMENT PRIMARY KEY,
    teacher_id       INT      NOT NULL,
    auto_generate    BOOLEAN  DEFAULT FALSE,
    target_students  TEXT,
    auto_difficulty  ENUM('easy','medium','hard','adaptive') DEFAULT 'medium',
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (teacher_id) REFERENCES teachers(user_id) ON DELETE CASCADE,
    UNIQUE KEY uniq_teacher_settings (teacher_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
