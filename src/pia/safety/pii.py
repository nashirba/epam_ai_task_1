"""PII redaction layer -- regex baseline (no Presidio / spaCy model dependency).

Recognised patterns for Kazakhstan personal data:

- **KZ IIN**: 12 consecutive digits at word boundary -> ``[IIN]``
- **Phone**: KZ mobile +7XXXXXXXXXX or 8XXXXXXXXXX (common separators allowed) -> ``[PHONE]``
- **IBAN**: KZ-format IBAN ``KZdd[A-Z0-9]{16}`` -> ``[IBAN]``
- **Email**: ``local@domain.tld`` -> ``[EMAIL]``

Order matters: PHONE is matched *before* IIN so that a ``+7…`` 11-digit number
is not mis-classified as an IIN.  IIN catches 12-digit sequences at word
boundaries.

False-positive note: a bare 12-digit number that is not a real IIN (e.g. an
account number) will also be redacted.  This is an acceptable conservative
choice for a financial advisory context — documented in ADR-0011.
"""

from __future__ import annotations

import re

# ---- Compiled patterns (compiled once at module load) ----

# KZ phone: +7 followed by 10 digits, or 8 followed by 10 digits.
# Allow spaces, dashes, parentheses as separators inside the digit groups.
# Important: match this BEFORE IIN to avoid treating "+7XXXXXXXXXX" as 12 digits.
_PHONE_RE = re.compile(
    r"(?<!\d)"  # not preceded by a digit
    r"(?:\+7|8)"  # country code
    r"[\s\-()]?"  # optional separator after country code
    r"\d{3}"  # area code
    r"[\s\-()]?"
    r"\d{3}"
    r"[\s\-]?"
    r"\d{2}"
    r"[\s\-]?"
    r"\d{2}"
    r"(?!\d)",  # not followed by a digit
)

# KZ IIN: exactly 12 consecutive digits at a word boundary.
# Must NOT match 13+ digit sequences (would be a different token).
_IIN_RE = re.compile(r"(?<!\d)\d{12}(?!\d)")

# KZ IBAN: KZ + 2 check digits + 16 alphanumeric chars (total 20 chars).
_IBAN_RE = re.compile(r"\bKZ\d{2}[A-Z0-9]{16}\b")

# Email: conservative but sufficient — local-part@domain.tld
_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")


def redact_pii(text: str) -> str:
    """Return *text* with PII tokens replaced by safe placeholders.

    Substitution order: phone → IIN → IBAN → email.
    """
    text = _PHONE_RE.sub("[PHONE]", text)
    text = _IIN_RE.sub("[IIN]", text)
    text = _IBAN_RE.sub("[IBAN]", text)
    text = _EMAIL_RE.sub("[EMAIL]", text)
    return text
