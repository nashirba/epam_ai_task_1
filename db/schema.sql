-- Database Schema: validation_rules
-- Stores validation rule metadata.
-- Note: Some rules may be code-based (regex_pattern can be NULL).

CREATE TABLE IF NOT EXISTS validation_rules (
  id SERIAL PRIMARY KEY,
  rule_name VARCHAR(100) NOT NULL UNIQUE,
  regex_pattern TEXT NULL,
  error_message TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Optional seed data (PostgreSQL). Adjust patterns/messages as needed.
INSERT INTO validation_rules (rule_name, regex_pattern, error_message)
VALUES
  ('email_format', '^[^\s@]+@[^\s@]+\.[^\s@]{2,}$', 'Email must be a valid email address.'),
  ('password_min_length', NULL, 'Password must be at least 8 characters long.'),
  ('password_has_number', NULL, 'Password must contain at least 1 number.'),
  ('password_has_special', NULL, 'Password must contain at least 1 special character.'),
  ('phone_e164', '^\+[1-9]\d{7,14}$', 'Phone number must be in international (E.164) format, e.g. +14155552671.')
ON CONFLICT (rule_name) DO NOTHING;
