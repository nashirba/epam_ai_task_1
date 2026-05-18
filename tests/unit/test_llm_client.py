from types import SimpleNamespace
from unittest.mock import patch

from pia.llm.client import LLMClient


def test_llm_client_chat_simple():
    fake = {"choices": [{"message": {"content": "hi"}}]}
    with patch("pia.llm.client.litellm.completion", return_value=fake):
        client = LLMClient(model="gemini/gemini-2.0-flash")
        out = client.chat([{"role": "user", "content": "hello"}])
    assert out["content"] == "hi"


def test_llm_client_normalizes_dict_tool_calls():
    fake = {
        "choices": [
            {
                "message": {
                    "content": "",
                    "tool_calls": [
                        {
                            "id": "call_1",
                            "function": {"name": "lookup", "arguments": '{"q": "NBK"}'},
                        }
                    ],
                }
            }
        ]
    }
    with patch("pia.llm.client.litellm.completion", return_value=fake):
        client = LLMClient(model="gemini/gemini-2.0-flash")
        out = client.chat([{"role": "user", "content": "hello"}], tools=[{"type": "function"}])
    assert out["tool_calls"] == [
        {"id": "call_1", "function": {"name": "lookup", "arguments": '{"q": "NBK"}'}}
    ]


def test_llm_client_passes_num_retries_to_litellm():
    fake = {"choices": [{"message": {"content": "hi"}}]}
    with patch("pia.llm.client.litellm.completion", return_value=fake) as mock_completion:
        client = LLMClient(model="gemini/gemini-2.0-flash", num_retries=5)
        client.chat([{"role": "user", "content": "hello"}])
    assert mock_completion.call_args.kwargs["num_retries"] == 5


def test_llm_client_normalizes_object_tool_calls():
    call = SimpleNamespace(
        id="call_2",
        function=SimpleNamespace(name="lookup", arguments='{"q": "KASE"}'),
    )
    message = SimpleNamespace(content="", tool_calls=[call])
    fake = {"choices": [{"message": message}]}
    with patch("pia.llm.client.litellm.completion", return_value=fake):
        client = LLMClient(model="gemini/gemini-2.0-flash")
        out = client.chat([{"role": "user", "content": "hello"}], tools=[{"type": "function"}])
    assert out["tool_calls"] == [
        {"id": "call_2", "function": {"name": "lookup", "arguments": '{"q": "KASE"}'}}
    ]
