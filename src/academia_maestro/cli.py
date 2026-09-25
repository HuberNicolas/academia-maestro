"""Command-line interface: upload research papers to ChatPDF and save its answers to a set of questions."""

import argparse
import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv

from .chatpdf import ChatPDF, ChatPDFError

log = logging.getLogger("academia_maestro")

DEFAULT_QUESTIONS = [
    "Provide a short summary: What is the paper about?",
    "What problem did they want to solve?",
    "What methodology did they use?",
    "What is the main contribution of the paper?",
    "What are the limitations?",
    "Despite the limitations, why is the paper still valuable?",
]


def read_questions(path: Path) -> list[str]:
    lines = (line.strip() for line in path.read_text(encoding="utf-8").splitlines())
    return [line for line in lines if line and not line.startswith("#")]


def load_sources(path: Path) -> dict[str, str]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def save_sources(path: Path, sources: dict[str, str]) -> None:
    path.write_text(json.dumps(sources, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def upload(client: ChatPDF, papers: Path, sources_file: Path) -> dict[str, str]:
    """Upload every PDF in ``papers`` that is not in ``sources_file`` yet; return all known sources."""
    sources = load_sources(sources_file)
    for pdf in sorted(papers.rglob("*.pdf", case_sensitive=False)):
        if pdf.name in sources:
            log.info("Already uploaded: %s", pdf.name)
            continue
        try:
            sources[pdf.name] = client.add_file(pdf)
        except ChatPDFError as e:
            log.error("Upload failed for %s: %s", pdf.name, e)
            continue
        log.info("Uploaded %s as %s", pdf.name, sources[pdf.name])
        save_sources(sources_file, sources)
    return sources


def ask(client: ChatPDF, sources: dict[str, str], questions: list[str], out: Path, overwrite: bool = False) -> None:
    """Ask every question about every source and write one JSON file per paper to ``out``."""
    out.mkdir(parents=True, exist_ok=True)
    for name, source_id in sorted(sources.items()):
        target = out / f"{Path(name).stem}.json"
        if target.exists() and not overwrite:
            log.info("Already answered: %s", target)
            continue
        answers = {}
        for question in questions:
            try:
                answers[question] = client.ask(source_id, question)
            except ChatPDFError as e:
                log.error("%s: %s", name, e)
                answers[question] = None
        target.write_text(json.dumps(answers, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        log.info("Saved %s", target)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="academia-maestro",
        description="Ask ChatPDF the same questions about many research papers and save the answers as JSON.",
    )
    parser.add_argument("--papers", type=Path, default=Path("Reading"), help="folder with PDFs (default: Reading)")
    parser.add_argument("--out", type=Path, default=Path("Summary"), help="folder for the answers (default: Summary)")
    parser.add_argument(
        "--sources", type=Path, default=Path("sources.json"), help="uploaded PDFs and their ChatPDF source IDs"
    )
    parser.add_argument(
        "--questions", type=Path, help="text file with one question per line (default: six general questions)"
    )
    parser.add_argument("--overwrite", action="store_true", help="ask again for papers that already have answers")
    parser.add_argument(
        "command",
        choices=["upload", "ask", "run"],
        help="upload: send new PDFs to ChatPDF; ask: save the answers; run: both",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    load_dotenv(".env")
    load_dotenv(".env.local", override=True)
    client = ChatPDF(os.getenv("CHATPDF_KEY", ""))

    if args.command in ("upload", "run"):
        upload(client, args.papers, args.sources)
    if args.command in ("ask", "run"):
        sources = load_sources(args.sources)
        if not sources:
            raise SystemExit(f"No uploaded papers in {args.sources}; run 'academia-maestro upload' first")
        questions = read_questions(args.questions) if args.questions else DEFAULT_QUESTIONS
        ask(client, sources, questions, args.out, args.overwrite)


if __name__ == "__main__":
    main()
