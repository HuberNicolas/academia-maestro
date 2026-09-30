"""Client for a local Ollama server (https://ollama.com). The PDF text is extracted locally and sent with each question."""

import os
from functools import cache
from pathlib import Path

import requests
from pypdf import PdfReader

from .provider import ProviderError

SYSTEM = (
    "You answer questions about the research paper below. "
    "Base your answer on the paper only and say so when it does not cover the question."
)


@cache
def pdf_text(path: str) -> str:
    return "\n\n".join(page.extract_text() or "" for page in PdfReader(path).pages).strip()


class Ollama:
    def __init__(self, model: str | None, host: str | None = None, num_ctx: int = 32768, timeout: float = 600):
        if not model:
            raise ProviderError("Ollama needs a model, e.g. --model qwen3 (see `ollama list`)")
        self.model = model
        self.url = (host or os.getenv("OLLAMA_HOST") or "http://localhost:11434").rstrip("/")
        if "://" not in self.url:
            self.url = f"http://{self.url}"
        # Ollama's default context is too small for a paper; raise it so the text is not cut off.
        self.num_ctx = num_ctx
        self.timeout = timeout

    def add_file(self, pdf: Path) -> str:
        """Nothing is uploaded: check that the PDF has text and return its path as the ID."""
        if not pdf_text(str(pdf)):
            raise ProviderError(f"{pdf.name} has no extractable text (scanned PDF?)")
        return str(pdf)

    def ask(self, source_id: str, question: str) -> str:
        # Same prefix for every question, so Ollama can reuse the processed paper between requests.
        messages = [
            {"role": "system", "content": f"{SYSTEM}\n\n<paper>\n{pdf_text(source_id)}\n</paper>"},
            {"role": "user", "content": question},
        ]
        data = {"model": self.model, "messages": messages, "stream": False, "options": {"num_ctx": self.num_ctx}}
        try:
            response = requests.post(f"{self.url}/api/chat", json=data, timeout=self.timeout)
            response.raise_for_status()
        except requests.RequestException as e:
            raise ProviderError(f"Ollama request failed: {e}") from e
        return response.json()["message"]["content"].strip()
