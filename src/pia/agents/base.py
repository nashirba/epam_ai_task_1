from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from pia.llm.client import LLMClient
from pia.observability import trace


@dataclass
class AgentRunResult:
    text: str
    tool_calls_made: list[str]  # ordered, possibly with repeats
    tool_errors: list[str]  # tool names whose handler raised
    budget_exhausted: bool


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict
    handler: Callable[..., Any]


@dataclass
class BaseAgent:
    name: str
    system_prompt: str
    tools: list[Tool] = field(default_factory=list)
    llm: LLMClient = field(default_factory=LLMClient)
    max_tool_calls: int = 5

    def _tool_schemas(self) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            }
            for t in self.tools
        ]

    @trace("agent.run")
    def run(self, user_message: str) -> AgentRunResult:
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_message},
        ]
        tool_calls_made: list[str] = []
        tool_errors: list[str] = []
        for _ in range(self.max_tool_calls):
            resp = self.llm.chat(messages, tools=self._tool_schemas() or None)
            if not resp["tool_calls"]:
                return AgentRunResult(
                    text=resp["content"],
                    tool_calls_made=tool_calls_made,
                    tool_errors=tool_errors,
                    budget_exhausted=False,
                )
            for call in resp["tool_calls"]:
                fn = call["function"]
                tool = next((t for t in self.tools if t.name == fn["name"]), None)
                if tool is None:
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": call["id"],
                            "content": f"Error: unknown tool {fn['name']}",
                        }
                    )
                    continue
                try:
                    args = json.loads(fn.get("arguments") or "{}")
                except json.JSONDecodeError as e:
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": call["id"],
                            "content": f"Error: invalid JSON args: {e}",
                        }
                    )
                    continue
                try:
                    result = tool.handler(**args)
                except Exception as e:  # noqa: BLE001 — degraded answer path
                    tool_errors.append(tool.name)
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": call["id"],
                            "content": f"ToolError: {type(e).__name__}: {e}",
                        }
                    )
                    continue
                tool_calls_made.append(tool.name)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call["id"],
                        "content": json.dumps(result, ensure_ascii=False, default=str),
                    }
                )
        return AgentRunResult(
            text=resp["content"] or "(no response — tool-call budget exhausted)",
            tool_calls_made=tool_calls_made,
            tool_errors=tool_errors,
            budget_exhausted=True,
        )
