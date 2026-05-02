# tests/unit/test_base_agent.py
from typing import Any
from unittest.mock import MagicMock

from pia.agents.base import BaseAgent, Tool


def _llm_responses(*responses):
    """Return a fake LLMClient whose chat() yields each scripted response in turn."""
    fake = MagicMock()
    iterator = iter(responses)
    fake.chat.side_effect = lambda messages, tools=None: next(iterator)
    return fake


def test_no_tool_calls_returns_content_immediately():
    agent = BaseAgent(
        name="t",
        system_prompt="sys",
        tools=[],
        llm=_llm_responses({"content": "hi", "tool_calls": []}),
    )
    out = agent.run("hello")
    assert out.text == "hi"
    assert out.tool_calls_made == []
    assert out.budget_exhausted is False


def test_unknown_tool_continues_with_error_message():
    """An unknown tool appends a tool error and the loop continues."""
    fake = _llm_responses(
        {
            "content": "",
            "tool_calls": [
                {"id": "1", "function": {"name": "ghost", "arguments": "{}"}},
            ],
        },
        {"content": "done after error", "tool_calls": []},
    )
    agent = BaseAgent(name="t", system_prompt="sys", tools=[], llm=fake)
    out = agent.run("hello")
    assert out.text == "done after error"
    assert out.tool_calls_made == []  # ghost did not execute
    assert "ghost" not in out.tool_errors
    assert out.budget_exhausted is False


def test_invalid_json_arguments_appends_error_and_continues():
    fake = _llm_responses(
        {
            "content": "",
            "tool_calls": [
                {"id": "1", "function": {"name": "ok", "arguments": "{not-json"}},
            ],
        },
        {"content": "recovered", "tool_calls": []},
    )
    tool = Tool(
        name="ok",
        description="",
        parameters={"type": "object"},
        handler=lambda **kw: {"ok": True},
    )
    agent = BaseAgent(name="t", system_prompt="sys", tools=[tool], llm=fake)
    out = agent.run("hello")
    assert out.text == "recovered"
    assert out.tool_calls_made == []  # invalid JSON args means handler never ran


def test_handler_exception_marks_tool_error_and_continues():
    def boom(**_kw: Any) -> dict:
        raise RuntimeError("upstream down")

    fake = _llm_responses(
        {
            "content": "",
            "tool_calls": [
                {"id": "1", "function": {"name": "boom", "arguments": "{}"}},
            ],
        },
        {"content": "graceful", "tool_calls": []},
    )
    tool = Tool(name="boom", description="", parameters={"type": "object"}, handler=boom)
    agent = BaseAgent(name="t", system_prompt="sys", tools=[tool], llm=fake)
    out = agent.run("hello")
    assert out.text == "graceful"
    assert "boom" in out.tool_errors


def test_budget_exhausted_returns_sentinel():
    """Looping tool calls return budget_exhausted=True with text."""
    tool = Tool(
        name="loop",
        description="",
        parameters={"type": "object"},
        handler=lambda **kw: {"k": 1},
    )
    # produce identical "tool_call only" responses every time
    fake = MagicMock()
    fake.chat.return_value = {
        "content": "still thinking",
        "tool_calls": [
            {"id": "1", "function": {"name": "loop", "arguments": "{}"}},
        ],
    }
    agent = BaseAgent(name="t", system_prompt="sys", tools=[tool], llm=fake, max_tool_calls=3)
    out = agent.run("hello")
    assert out.budget_exhausted is True
    assert out.tool_calls_made.count("loop") == 3  # exactly max_tool_calls executions
