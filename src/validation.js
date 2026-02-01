'use strict';

/**
 * Data Validation Module
 * Validates: email, password, phone
 * Return format (all functions): { valid: boolean, errors: string[] }
 */

// Practical email regex (not full RFC 5322, but common in production)
const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

// E.164: + followed by 8 to 15 digits (country code + subscriber number)
const E164_PHONE_REGEX = /^\+[1-9]\d{7,14}$/;

function isNonEmptyString(value) {
  return typeof value === 'string' && value.trim().length > 0;
}

function asStringOrNull(value) {
  // Normalizes unknown inputs without throwing, so validators can return errors cleanly.
  if (value === null || value === undefined) return null;
  if (typeof value === 'string') return value;
  // If caller passed a number/boolean/object, treat as invalid type (null triggers "required" message).
  return null;
}

function validateEmail(email) {
  const errors = [];
  const value = asStringOrNull(email);

  if (!isNonEmptyString(value)) {
    errors.push('Email is required.');
    return { valid: false, errors };
  }

  const trimmed = value.trim();
  if (!EMAIL_REGEX.test(trimmed)) {
    errors.push('Email must be a valid email address.');
  }

  return { valid: errors.length === 0, errors };
}

function validatePassword(password) {
  const errors = [];
  const value = asStringOrNull(password);

  if (!isNonEmptyString(value)) {
    errors.push('Password is required.');
    return { valid: false, errors };
  }

  // Do not trim passwords; spaces may be intentional.
  const pwd = value;

  if (pwd.length < 8) {
    errors.push('Password must be at least 8 characters long.');
  }

  if (!/\d/.test(pwd)) {
    errors.push('Password must contain at least 1 number.');
  }

  // "Special character" = anything not a letter/digit/underscore/whitespace.
  if (!/[^\w\s]/.test(pwd)) {
    errors.push('Password must contain at least 1 special character.');
  }

  return { valid: errors.length === 0, errors };
}

function validatePhone(phone) {
  const errors = [];
  const value = asStringOrNull(phone);

  if (!isNonEmptyString(value)) {
    errors.push('Phone number is required.');
    return { valid: false, errors };
  }

  const trimmed = value.trim();
  if (!E164_PHONE_REGEX.test(trimmed)) {
    errors.push('Phone number must be in international (E.164) format, e.g. +14155552671.');
  }

  return { valid: errors.length === 0, errors };
}

/**
 * Convenience validator for API usage.
 * Accepts { email, password, phone } and returns combined result.
 */
function validateAll(payload = {}) {
  const errors = [];

  const emailRes = validateEmail(payload.email);
  const passRes = validatePassword(payload.password);
  const phoneRes = validatePhone(payload.phone);

  errors.push(...emailRes.errors, ...passRes.errors, ...phoneRes.errors);
  return { valid: errors.length === 0, errors };
}

module.exports = {
  validateEmail,
  validatePassword,
  validatePhone,
  validateAll,
  _regex: { EMAIL_REGEX, E164_PHONE_REGEX }
};
