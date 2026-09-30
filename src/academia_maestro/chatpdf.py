"""Minimal client for the ChatPDF API (https://www.chatpdf.com/docs/api/backend)."""

from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .provider import ProviderError

API_URL = "https://api.chatpdf.com/v1"


class ChatPDFError(ProviderError):
    pass


class ChatPDF:
    def __init__(self, api_key: str, timeout: float = 120, session: requests.Session | None = None):
        if not api_key:
            raise ChatPDFError("CHATPDF_KEY is not set; see .env.example")
        self.timeout = timeout
        self.session = session or requests.Session()
        self.session.headers["x-api-key"] = api_key
        # Retry rate limits and server errors with backoff; POST is safe to repeat here.
        retry = Retry(total=4, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504], allowed_methods=None)
        self.session.mount("https://", HTTPAdapter(max_retries=retry))

    def _post(self, path: str, **kwargs) -> dict:
        try:
            response = self.session.post(f"{API_URL}{path}", timeout=self.timeout, **kwargs)
        except requests.RequestException as e:
            raise ChatPDFError(f"{path} failed: {e}") from e
        if response.status_code != 200:
            raise ChatPDFError(f"{path} failed with {response.status_code}: {response.text}")
        return response.json() if response.content else {}

    def add_file(self, pdf: Path) -> str:
        """Upload a PDF and return its source ID."""
        with pdf.open("rb") as f:
            return self._post("/sources/add-file", files={"file": (pdf.name, f, "application/pdf")})["sourceId"]

    def ask(self, source_id: str, question: str) -> str:
        """Ask one question about an uploaded PDF and return the answer."""
        data = {"sourceId": source_id, "messages": [{"role": "user", "content": question}]}
        return self._post("/chats/message", json=data)["content"]

    def delete(self, source_ids: list[str]) -> None:
        self._post("/sources/delete", json={"sources": source_ids})
