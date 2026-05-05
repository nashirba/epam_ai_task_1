from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Chunk:
    text: str
    headings: tuple[str, ...]


_TOKEN_RE = re.compile(r"\S+")


def _approx_tokens(s: str) -> int:
    return len(_TOKEN_RE.findall(s))


def _emit(buf: list[str], headings: tuple[str, ...]) -> Chunk:
    """Build a Chunk, prepending the leaf heading text into the body so BM25
    can match entities mentioned only in the heading.

    The leaf heading is added as plain text (no ``#`` prefix) — the structural
    breadcrumb is still carried on ``Chunk.headings`` for retrieval-side use.
    """
    body = "\n\n".join(buf)
    leaf = headings[-1] if headings else ""
    if leaf and not body.startswith(leaf):
        body = f"{leaf}\n\n{body}" if body else leaf
    return Chunk(body, headings)


def chunk_markdown(text: str, *, max_tokens: int = 300, overlap_tokens: int = 80) -> list[Chunk]:
    """Heading-aware chunker. Splits on blank-line paragraphs, accumulates up to
    `max_tokens`, then carries `overlap_tokens` tail into the next chunk.
    Tracks the heading stack so each chunk knows its breadcrumb; the leaf
    heading text is also prepended into the chunk body to help BM25 recall."""
    paragraphs: list[tuple[str, tuple[str, ...]]] = []
    stack: list[tuple[int, str]] = []  # (level, text)
    for para in re.split(r"\n\s*\n", text.strip()):
        m = re.match(r"^(#{1,6})\s+(.*)$", para.strip())
        if m:
            level = len(m.group(1))
            heading = m.group(2).strip()
            stack = [(lvl, t) for lvl, t in stack if lvl < level]
            stack.append((level, heading))
            continue
        paragraphs.append((para.strip(), tuple(t for _, t in stack)))

    chunks: list[Chunk] = []
    buf: list[str] = []
    buf_tokens = 0
    last_headings: tuple[str, ...] = ()
    for para, headings in paragraphs:
        n = _approx_tokens(para)
        if buf and buf_tokens + n > max_tokens:
            chunks.append(_emit(buf, last_headings))
            tail = " ".join(" ".join(buf).split()[-overlap_tokens:])
            buf = [tail] if tail else []
            buf_tokens = _approx_tokens(tail) if tail else 0
        buf.append(para)
        buf_tokens += n
        last_headings = headings
    if buf:
        chunks.append(_emit(buf, last_headings))
    return chunks
