# API Specification — Validation Service

This document specifies two REST endpoints:

- `POST /validate` — validates input data
- `GET /validation-rules` — returns all validation rules

> Implementation note: This repo includes an **optional** Express server (`src/server.js`) that demonstrates these endpoints.
> In a real deployment, `GET /validation-rules` would query the database table defined in `db/schema.sql`.

---

## 1) POST /validate

### Purpose
Validate user inputs for `email`, `password`, and `phone`.

### Request
- Method: `POST`
- Path: `/validate`
- Headers: `Content-Type: application/json`
- Body:

```json
{
  "email": "user@example.com",
  "password": "Abc!1234",
  "phone": "+14155552671"
}
```

### Responses

#### 200 OK (validation passed)
```json
{ "valid": true, "errors": [] }
```

#### 422 Unprocessable Entity (validation failed)
```json
{
  "valid": false,
  "errors": [
    "Password must contain at least 1 special character."
  ]
}
```

#### 400 Bad Request (invalid/missing JSON body)
```json
{
  "valid": false,
  "errors": ["Request body must be JSON."]
}
```

---

## 2) GET /validation-rules

### Purpose
Return the list of validation rules (rule name, regex pattern (if any), error message).

### Request
- Method: `GET`
- Path: `/validation-rules`

### Responses

#### 200 OK
```json
{
  "rules": [
    {
      "id": 1,
      "rule_name": "email_format",
      "regex_pattern": "^[^\\s@]+@[^\\s@]+\\.[^\\s@]{2,}$",
      "error_message": "Email must be a valid email address."
    }
  ]
}
```

---

## Error Codes Summary
- `200` OK — validation passed / rules fetched
- `400` Bad Request — request is not valid JSON
- `422` Unprocessable Entity — validation failed
- `500` Internal Server Error — unexpected server error
