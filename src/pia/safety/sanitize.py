"""Input sanitiser for PIA.

``sanitize_input`` is the first layer in the safety facade:
  1. Strip ASCII control characters (0x00-0x1F, 0x7F), preserving \\n and \\t.
  2. Normalize Unicode to NFKC.
  3. Trim leading/trailing whitespace.
  4. Cap to 8 000 characters (silent truncation).
"""
from __future__ import annotations

import re
import unicodedata

# Match control chars except TAB (0x09) and LF (0x0A)
_CTRL_RE = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")
_MAX_LEN = 8_000


def sanitize_input(text: str) -> str:
    """Return a sanitised version of *text* safe for downstream processing."""
    text = _CTRL_RE.sub("", text)
    text = unicodedata.normalize("NFKC", text)
    text = text.strip()
    return text[:_MAX_LEN]
