from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import litellm

from pia.config import get_settings


@dataclass
class LLMClient:
    model: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None

    def __post_init__(self) -> None:
        s = get_settings()
        self.model = self.model or s.llm_model
        self.temperature = self.temperature if self.temperature is not None else s.llm_temperature
        self.max_tokens = self.max_tokens or s.llm_max_tokens

    def chat(self, messages: list[dict[str, Any]], tools: list[dict] | None = None) -> dict:
        kwargs: dict[str, Any] = dict(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        resp = litellm.completion(**kwargs)
        msg = resp["choices"][0]["message"]
        return {
            "content": msg.get("content") or "",
            "tool_calls": msg.get("tool_calls") or [],
        }
