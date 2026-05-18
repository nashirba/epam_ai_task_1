from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import litellm

from pia.config import get_settings
from pia.observability import trace


def _field(obj: Any, name: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _normalize_tool_call(call: Any) -> dict[str, Any]:
    function = _field(call, "function", {})
    arguments = _field(function, "arguments", "{}")
    if not isinstance(arguments, str):
        arguments = str(arguments)
    return {
        "id": _field(call, "id", ""),
        "function": {
            "name": _field(function, "name", ""),
            "arguments": arguments,
        },
    }


@dataclass
class LLMClient:
    model: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    num_retries: int | None = None

    def __post_init__(self) -> None:
        s = get_settings()
        self.model = self.model or s.llm_model
        self.temperature = self.temperature if self.temperature is not None else s.llm_temperature
        self.max_tokens = self.max_tokens or s.llm_max_tokens
        if self.num_retries is None:
            self.num_retries = s.llm_num_retries

    @trace("llm.chat")
    def chat(self, messages: list[dict[str, Any]], tools: list[dict] | None = None) -> dict:
        kwargs: dict[str, Any] = dict(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            num_retries=self.num_retries,
        )
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        resp = litellm.completion(**kwargs)
        msg = resp["choices"][0]["message"]
        tool_calls = [_normalize_tool_call(call) for call in (_field(msg, "tool_calls", []) or [])]
        return {
            "content": _field(msg, "content", "") or "",
            "tool_calls": tool_calls,
        }
