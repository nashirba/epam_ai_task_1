from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Citation(BaseModel):
    source: str
    source_url: str
    published_at: str | None = None
    snippet: str | None = None
    score: float | None = None


class PortfolioQuery(BaseModel):
    question: str
    asset_class: str | None = None
    ticker: str | None = None


class PortfolioAnswer(BaseModel):
    text: str
    citations: list[Citation] = []
    used_holdings: bool = False


class MarketQuery(BaseModel):
    question: str
    tickers: list[str] = []


class MarketSource(BaseModel):
    tool: str
    url: str | None = None
    last_updated: str | None = None


class MarketAnswer(BaseModel):
    text: str
    sources: list[MarketSource] = []
    degraded: bool = False  # set when an upstream tool failed


class Action(BaseModel):
    summary: str
    rationale: str


class Recommendation(BaseModel):
    summary: str
    actions: list[Action] = []
    citations: list[Citation] = []
    market_sources: list[MarketSource] = []
    disclaimer: str = (
        "This is informational only and not licensed financial, legal, or tax advice. "
        "Consult a licensed professional before acting."
    )


class AgentMessage(BaseModel):
    request_id: UUID = Field(default_factory=uuid4)
    sender: str
    receiver: str
    issued_at: datetime = Field(default_factory=_utcnow)
    payload: BaseModel  # one of the *Query / *Answer / Recommendation types

    model_config = {"arbitrary_types_allowed": True}
