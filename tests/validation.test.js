'use strict';

const {
  validateEmail,
  validatePassword,
  validatePhone,
  validateAll,
} = require('../src/validation');

describe('validateEmail()', () => {
  test('valid email passes', () => {
    expect(validateEmail('user@example.com')).toEqual({ valid: true, errors: [] });
  });

  test('empty string fails required', () => {
    const res = validateEmail('');
    expect(res.valid).toBe(false);
    expect(res.errors).toContain('Email is required.');
  });

  test('null fails required', () => {
    const res = validateEmail(null);
    expect(res.valid).toBe(false);
    expect(res.errors).toContain('Email is required.');
  });

  test('non-string type fails required', () => {
    const res = validateEmail(12345);
    expect(res.valid).toBe(false);
    expect(res.errors).toContain('Email is required.');
  });

  test('invalid format fails', () => {
    const res = validateEmail('not-an-email');
    expect(res.valid).toBe(false);
    expect(res.errors).toContain('Email must be a valid email address.');
  });

  test('email with surrounding spaces is trimmed and valid', () => {
    expect(validateEmail('  user@example.com  ')).toEqual({ valid: true, errors: [] });
  });
});

describe('validatePassword()', () => {
  test('valid password passes', () => {
    expect(validatePassword('Abc!1234')).toEqual({ valid: true, errors: [] });
  });

  test('too short fails length rule', () => {
    const res = validatePassword('A!1a');
    expect(res.valid).toBe(false);
    expect(res.errors).toContain('Password must be at least 8 characters long.');
  });

  test('missing number fails', () => {
    const res = validatePassword('Abc!defg');
    expect(res.valid).toBe(false);
    expect(res.errors).toContain('Password must contain at least 1 number.');
  });

  test('missing special char fails', () => {
    const res = validatePassword('Abcdefg1');
    expect(res.valid).toBe(false);
    expect(res.errors).toContain('Password must contain at least 1 special character.');
  });

  test('empty string fails required', () => {
    const res = validatePassword('');
    expect(res.valid).toBe(false);
    expect(res.errors).toContain('Password is required.');
  });

  test('null fails required', () => {
    const res = validatePassword(null);
    expect(res.valid).toBe(false);
    expect(res.errors).toContain('Password is required.');
  });

  test('special characters allowed, still valid', () => {
    const res = validatePassword('P@ssw0rd!');
    expect(res).toEqual({ valid: true, errors: [] });
  });
});

describe('validatePhone()', () => {
  test('valid E.164 phone passes', () => {
    expect(validatePhone('+14155552671')).toEqual({ valid: true, errors: [] });
  });

  test('missing + fails', () => {
    const res = validatePhone('14155552671');
    expect(res.valid).toBe(false);
    expect(res.errors[0]).toMatch(/E\.164/);
  });

  test('too short fails', () => {
    const res = validatePhone('+123');
    expect(res.valid).toBe(false);
    expect(res.errors[0]).toMatch(/E\.164/);
  });

  test('empty string fails required', () => {
    const res = validatePhone('');
    expect(res.valid).toBe(false);
    expect(res.errors).toContain('Phone number is required.');
  });

  test('null fails required', () => {
    const res = validatePhone(null);
    expect(res.valid).toBe(false);
    expect(res.errors).toContain('Phone number is required.');
  });

  test('non-string type fails required', () => {
    const res = validatePhone({ phone: '+14155552671' });
    expect(res.valid).toBe(false);
    expect(res.errors).toContain('Phone number is required.');
  });
});

describe('validateAll()', () => {
  test('all valid passes', () => {
    const res = validateAll({
      email: 'user@example.com',
      password: 'Abc!1234',
      phone: '+14155552671',
    });
    expect(res).toEqual({ valid: true, errors: [] });
  });

  test('collects multiple errors', () => {
    const res = validateAll({
      email: 'bad',
      password: 'short',
      phone: '123',
    });
    expect(res.valid).toBe(false);
    expect(res.errors.length).toBeGreaterThanOrEqual(3);
  });
});
