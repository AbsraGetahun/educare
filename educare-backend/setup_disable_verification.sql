-- Optional: mark all existing users as verified (safe to run after removing email verification)
UPDATE users SET is_verified = TRUE WHERE is_verified IS NULL OR is_verified = FALSE;
