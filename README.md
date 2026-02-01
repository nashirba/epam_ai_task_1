# Task 1 — Data Validation Module (Email / Password / Phone)

## Overview
This project provides:
- A validation module (`src/validation.js`) with:
  - `validateEmail()`
  - `validatePassword()`
  - `validatePhone()`
  - `validateAll()` (convenience function for API use)
- Database schema for storing validation rule metadata (`db/schema.sql`)
- API specification (`API_SPEC.md`)
- Jest unit tests (10+ cases) (`tests/validation.test.js`)
- Requirements document (`REQUIREMENTS.md`)
- Optional Express demo server (`src/server.js`)

All validators return:
```json
{ "valid": true, "errors": [] }
```

## Installation
Requires Node.js 18+ recommended.

```bash
npm install
```

## Usage Examples

### Using the module
```js
const { validateEmail, validatePassword, validatePhone, validateAll } = require('./src/validation');

console.log(validateEmail('user@example.com'));
console.log(validatePassword('Abc!1234'));
console.log(validatePhone('+14155552671'));

console.log(validateAll({
  email: 'user@example.com',
  password: 'Abc!1234',
  phone: '+14155552671'
}));
```

### Run tests
```bash
npm test
```

### Run API server (optional)
```bash
npm run dev
# http://localhost:3000
```

## API Endpoints
See **API_SPEC.md** for full details.

- `POST /validate`
- `GET /validation-rules`

## Error Codes
- `200` OK — validation passed / rules fetched
- `400` Bad Request — request is not valid JSON
- `422` Unprocessable Entity — validation failed
- `500` Internal Server Error — unexpected server error

## Example curl
```bash
curl -X POST http://localhost:3000/validate \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"Abc!1234","phone":"+14155552671"}'
```

## Security / Performance / Code Quality Review (Refinement Evidence)

### Security
- Validation functions are **pure** (no SQL, no DOM/HTML), so they do not introduce SQL injection or XSS directly.
- Regex patterns are anchored and simple to reduce **ReDoS** risk.
- API limits JSON body size (`10kb`) to reduce abuse.

### Performance
- Validators are O(n) over input length with very small constant factors.
- For sustained high throughput (e.g., ~1000 req/s), deploy behind a reverse proxy with:
  - multiple Node processes (PM2/cluster),
  - request rate limiting,
  - keep-alive enabled.

### Code Quality
- Consistent return type `{ valid, errors }` across all validators.
- Helper functions normalize unknown inputs and avoid throws from unexpected types.
