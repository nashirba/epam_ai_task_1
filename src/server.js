'use strict';

const express = require('express');
const { validateAll } = require('./validation');

const app = express();
app.use(express.json({ limit: '10kb' }));

// Example rules payload (in production, fetch from DB using parameterized queries).
app.get('/validation-rules', async (_req, res) => {
  return res.status(200).json({
    rules: [
      { rule_name: 'email_format', regex_pattern: '^[^\\s@]+@[^\\s@]+\\.[^\\s@]{2,}$', error_message: 'Email must be a valid email address.' },
      { rule_name: 'password_min_length', regex_pattern: null, error_message: 'Password must be at least 8 characters long.' },
      { rule_name: 'password_has_number', regex_pattern: null, error_message: 'Password must contain at least 1 number.' },
      { rule_name: 'password_has_special', regex_pattern: null, error_message: 'Password must contain at least 1 special character.' },
      { rule_name: 'phone_e164', regex_pattern: '^\\+[1-9]\\d{7,14}$', error_message: 'Phone number must be in international (E.164) format, e.g. +14155552671.' }
    ]
  });
});

app.post('/validate', (req, res) => {
  if (!req.body || typeof req.body !== 'object') {
    return res.status(400).json({ valid: false, errors: ['Request body must be JSON.'] });
  }

  const result = validateAll(req.body);
  if (!result.valid) {
    return res.status(422).json(result);
  }

  return res.status(200).json(result);
});

// Generic error handler
app.use((err, _req, res, _next) => {
  return res.status(500).json({ valid: false, errors: ['Internal server error.'] });
});

const port = process.env.PORT || 3000;
if (require.main === module) {
  app.listen(port, () => console.log(`Server running on port ${port}`));
}

module.exports = app;
