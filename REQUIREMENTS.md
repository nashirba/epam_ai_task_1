# Requirements Document — Data Validation Module

## Objective
Validate user input for **email**, **password**, and **phone** using custom rules and clear error messages.

## Return Format (All Validators)
All validation functions MUST return:

```json
{ "valid": true, "errors": [] }
```

- `valid`: boolean
- `errors`: array of strings (human-readable error messages)

## Validation Rules

| Field | Rule | Criteria | Error message |
|---|---|---|---|
| email | Required | Must be a non-empty string | `Email is required.` |
| email | Format | Must be a valid email format | `Email must be a valid email address.` |
| password | Required | Must be a non-empty string | `Password is required.` |
| password | Length | At least 8 characters | `Password must be at least 8 characters long.` |
| password | Number | Must include at least 1 digit | `Password must contain at least 1 number.` |
| password | Special char | Must include at least 1 special character | `Password must contain at least 1 special character.` |
| phone | Required | Must be a non-empty string | `Phone number is required.` |
| phone | International format | Must be E.164 format: `+` then 8–15 digits | `Phone number must be in international (E.164) format, e.g. +14155552671.` |

## Notes / Assumptions
- **Email**: Uses a practical, production-common email regex (not fully RFC 5322).
- **Phone**: Validates a normalized E.164-like string (recommended storage format).
- **Password**: Passwords are not trimmed; whitespace may be intentional.
