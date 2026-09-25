import json

from academia_maestro.chatpdf import ChatPDFError
from academia_maestro.cli import ask, read_questions, upload


class FakeClient:
    def __init__(self):
        self.uploaded = []

    def add_file(self, pdf):
        self.uploaded.append(pdf.name)
        return f"src_{pdf.stem}"

    def ask(self, source_id, question):
        if "fail" in question:
            raise ChatPDFError("boom")
        return f"{source_id}: {question}"


def test_read_questions_skips_comments_and_blank_lines(tmp_path):
    path = tmp_path / "q.txt"
    path.write_text("# comment\nFirst?\n\n  Second?  \n")
    assert read_questions(path) == ["First?", "Second?"]


def test_upload_skips_known_papers(tmp_path):
    papers = tmp_path / "Reading"
    (papers / "sub").mkdir(parents=True)
    (papers / "a.pdf").write_bytes(b"%PDF")
    (papers / "sub" / "b.PDF").write_bytes(b"%PDF")
    (papers / "notes.txt").write_text("x")
    sources_file = tmp_path / "sources.json"
    sources_file.write_text(json.dumps({"a.pdf": "src_old"}))

    client = FakeClient()
    sources = upload(client, papers, sources_file)

    assert client.uploaded == ["b.PDF"]
    assert sources == {"a.pdf": "src_old", "b.PDF": "src_b"}
    assert json.loads(sources_file.read_text()) == sources


def test_ask_writes_one_file_per_paper(tmp_path):
    out = tmp_path / "Summary"
    ask(FakeClient(), {"paper.pdf": "src_p"}, ["Why?", "fail?"], out)
    assert json.loads((out / "paper.json").read_text()) == {"Why?": "src_p: Why?", "fail?": None}
