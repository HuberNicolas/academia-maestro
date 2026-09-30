import csv
import json

from academia_maestro.chatpdf import ChatPDFError
from academia_maestro.cli import ask, parse_args, read_questions, table, upload


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


def test_ask_only_repeats_missing_and_failed_answers(tmp_path):
    out = tmp_path / "Summary"
    out.mkdir()
    (out / "paper.json").write_text(json.dumps({"Old?": "kept", "Retry?": None}))

    asked = []

    class Recorder(FakeClient):
        def ask(self, source_id, question):
            asked.append(question)
            return super().ask(source_id, question)

    ask(Recorder(), {"paper.pdf": "src_p"}, ["Old?", "Retry?", "New?"], out)

    assert sorted(asked) == ["New?", "Retry?"]
    assert json.loads((out / "paper.json").read_text()) == {
        "Old?": "kept",
        "Retry?": "src_p: Retry?",
        "New?": "src_p: New?",
    }


def test_default_sources_file_depends_on_provider():
    assert parse_args(["ask"]).sources.name == "sources.json"
    args = parse_args(["--provider", "ollama", "ask"])
    assert args.sources.name == "sources-ollama.json"
    assert args.workers == 1


def test_table_has_one_row_per_paper_and_one_column_per_question(tmp_path):
    out = tmp_path / "Summary"
    out.mkdir()
    (out / "a.json").write_text(json.dumps({"Why?": "A why", "How?": None}))
    (out / "b.json").write_text(json.dumps({"Why?": "B why", "Gap?": "B gap"}))

    table(out, tmp_path / "Summary.csv")

    with (tmp_path / "Summary.csv").open(encoding="utf-8-sig", newline="") as f:
        assert list(csv.reader(f)) == [
            ["Paper", "Why?", "How?", "Gap?"],
            ["a", "A why", "", ""],
            ["b", "B why", "", "B gap"],
        ]
