"""Client for Claude (https://docs.claude.com): PDFs go to the Files API and are read natively, figures included."""

from pathlib import Path

import anthropic

from .provider import ProviderError

DEFAULT_MODEL = "claude-opus-5"

SYSTEM = (
    "You answer questions about the attached research paper. "
    "Base your answer on the paper only and say so when it does not cover the question. "
    "Answer in plain prose without headings."
)


class Claude:
    def __init__(self, api_key: str | None = None, model: str = DEFAULT_MODEL):
        # Without a key, the SDK falls back to ANTHROPIC_AUTH_TOKEN or an `ant auth login` profile.
        self.client = anthropic.Anthropic(api_key=api_key or None, max_retries=4)
        self.model = model

    def add_file(self, pdf: Path) -> str:
        """Upload a PDF to the Files API and return its file ID."""
        try:
            return self.client.files.upload(file=(pdf.name, pdf.read_bytes(), "application/pdf")).id
        except anthropic.APIError as e:
            raise ProviderError(f"upload of {pdf.name} failed: {e}") from e

    def ask(self, source_id: str, question: str) -> str:
        """Ask one question about an uploaded PDF and return the answer."""
        # The paper comes first and is cached, so every further question about it reads it from the cache.
        document = {
            "type": "document",
            "source": {"type": "file", "file_id": source_id},
            "cache_control": {"type": "ephemeral"},
        }
        try:
            response = self.client.beta.messages.create(
                model=self.model,
                max_tokens=16000,
                system=SYSTEM,
                messages=[{"role": "user", "content": [document, {"type": "text", "text": question}]}],
                # If the model declines, the API retries the request on a fallback model.
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
            )
        except anthropic.APIError as e:
            raise ProviderError(str(e)) from e
        if response.stop_reason == "refusal":
            raise ProviderError(f"refused: {question}")
        return "".join(block.text for block in response.content if block.type == "text").strip()

    def delete(self, source_ids: list[str]) -> None:
        for source_id in source_ids:
            self.client.files.delete(source_id)
