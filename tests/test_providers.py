from types import SimpleNamespace

import pytest

from academia_maestro import claude, ollama
from academia_maestro.provider import ProviderError


class FakeMessages:
    def __init__(self, response):
        self.response = response
        self.kwargs = None

    def create(self, **kwargs):
        self.kwargs = kwargs
        return self.response


def fake_claude(response):
    client = claude.Claude(api_key="test")
    messages = FakeMessages(response)
    client.client = SimpleNamespace(beta=SimpleNamespace(messages=messages))
    return client, messages


def test_claude_sends_cached_document_before_question():
    text = SimpleNamespace(type="text", text=" Answer. ")
    client, messages = fake_claude(SimpleNamespace(stop_reason="end_turn", content=[text]))

    assert client.ask("file_1", "Why?") == "Answer."
    document, question = messages.kwargs["messages"][0]["content"]
    assert document["source"] == {"type": "file", "file_id": "file_1"}
    assert document["cache_control"] == {"type": "ephemeral"}
    assert question == {"type": "text", "text": "Why?"}
    assert messages.kwargs["model"] == claude.DEFAULT_MODEL


def test_claude_refusal_is_an_error():
    client, _ = fake_claude(SimpleNamespace(stop_reason="refusal", content=[]))
    with pytest.raises(ProviderError):
        client.ask("file_1", "Why?")


def test_ollama_needs_a_model():
    with pytest.raises(ProviderError):
        ollama.Ollama(None)


def test_ollama_sends_paper_text_and_question(monkeypatch):
    monkeypatch.setattr(ollama, "pdf_text", lambda path: "Paper text")
    sent = {}

    def post(url, json, timeout):
        sent.update(url=url, json=json)
        return SimpleNamespace(raise_for_status=lambda: None, json=lambda: {"message": {"content": "Local answer"}})

    monkeypatch.setattr(ollama.requests, "post", post)
    client = ollama.Ollama("qwen3", host="localhost:11434")

    assert client.ask("paper.pdf", "Why?") == "Local answer"
    assert sent["url"] == "http://localhost:11434/api/chat"
    system, user = sent["json"]["messages"]
    assert "Paper text" in system["content"]
    assert user == {"role": "user", "content": "Why?"}
