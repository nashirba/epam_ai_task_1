from unittest.mock import patch

from pia.llm.client import LLMClient


def test_llm_client_chat_simple():
    fake = {"choices": [{"message": {"content": "hi"}}]}
    with patch("pia.llm.client.litellm.completion", return_value=fake):
        client = LLMClient(model="gemini/gemini-2.0-flash")
        out = client.chat([{"role": "user", "content": "hello"}])
    assert out["content"] == "hi"
