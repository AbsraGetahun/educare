-- ============================================================
-- EDUCARE: Student Materials Assignment Table
-- Creates junction table to track which materials are assigned
-- to which students for targeted material delivery
-- ============================================================

-- Create student_materials junction table
CREATE TABLE IF NOT EXISTS student_materials (
    id INT AUTO_INCREMENT PRIMARY KEY,
    material_id INT NOT NULL,
    student_id INT NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (material_id) REFERENCES material(material_id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES students(user_id) ON DELETE CASCADE,
    UNIQUE KEY unique_assignment (material_id, student_id),
    INDEX idx_student (student_id),
    INDEX idx_material (material_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Verify table creation
SELECT 'student_materials table created successfully' AS status;

-- Show table structure
DESCRIBE student_materials;
