"""Minimal client for the ChatPDF API (https://www.chatpdf.com/docs/api/backend)."""

from pathlib import Path

import requests

API_URL = "https://api.chatpdf.com/v1"


class ChatPDFError(RuntimeError):
    pass


class ChatPDF:
    def __init__(self, api_key: str, timeout: float = 120, session: requests.Session | None = None):
        if not api_key:
            raise ChatPDFError("CHATPDF_KEY is not set; see .env.example")
        self.timeout = timeout
        self.session = session or requests.Session()
        self.session.headers["x-api-key"] = api_key

    def _post(self, path: str, **kwargs) -> dict:
        response = self.session.post(f"{API_URL}{path}", timeout=self.timeout, **kwargs)
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
