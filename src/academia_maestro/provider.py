"""What the CLI needs from a PDF question-answering service."""

from pathlib import Path
from typing import Protocol


class ProviderError(RuntimeError):
    pass


class Provider(Protocol):
    def add_file(self, pdf: Path) -> str:
        """Upload a PDF and return an ID for it."""
        ...

    def ask(self, source_id: str, question: str) -> str:
        """Ask one question about an uploaded PDF and return the answer."""
        ...
