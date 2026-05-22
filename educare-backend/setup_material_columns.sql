-- Extra citation columns on material table
ALTER TABLE material ADD COLUMN IF NOT EXISTS source_file VARCHAR(255);
ALTER TABLE material ADD COLUMN IF NOT EXISTS source_page INT;
ALTER TABLE material ADD COLUMN IF NOT EXISTS source_grade INT;
ALTER TABLE material ADD COLUMN IF NOT EXISTS section_title VARCHAR(255);
ALTER TABLE material ADD COLUMN IF NOT EXISTS helpful_count INT DEFAULT 0;
ALTER TABLE material ADD COLUMN IF NOT EXISTS not_helpful_count INT DEFAULT 0;
