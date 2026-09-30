"""Command-line interface: upload research papers and save the answers to a set of questions."""

import argparse
import csv
import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from dotenv import load_dotenv

from .provider import Provider, ProviderError

log = logging.getLogger("academia_maestro")

PROVIDERS = ["chatpdf", "claude", "ollama"]

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


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def upload(client: Provider, papers: Path, sources_file: Path) -> dict[str, str]:
    """Upload every PDF in ``papers`` that is not in ``sources_file`` yet; return all known sources."""
    sources = read_json(sources_file)
    for pdf in sorted(papers.rglob("*.pdf", case_sensitive=False)):
        if pdf.name in sources:
            log.info("Already uploaded: %s", pdf.name)
            continue
        try:
            sources[pdf.name] = client.add_file(pdf)
        except ProviderError as e:
            log.error("Upload failed for %s: %s", pdf.name, e)
            continue
        log.info("Uploaded %s as %s", pdf.name, sources[pdf.name])
        write_json(sources_file, dict(sorted(sources.items())))
    return sources


def ask(
    client: Provider,
    sources: dict[str, str],
    questions: list[str],
    out: Path,
    overwrite: bool = False,
    workers: int = 4,
) -> None:
    """Ask every question about every source and write one JSON file per paper to ``out``.

    Existing answers are kept; only questions that are new or failed before (``null``) are asked again.
    """
    out.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for name, source_id in sorted(sources.items()):
            target = out / f"{Path(name).stem}.json"
            answers = {} if overwrite else read_json(target)
            todo = [q for q in questions if answers.get(q) is None]
            if not todo:
                log.info("Already answered: %s", target)
                continue

            def one(question: str, name=name, source_id=source_id) -> str | None:
                try:
                    return client.ask(source_id, question)
                except ProviderError as e:
                    log.error("%s: %s", name, e)
                    return None

            # The first question runs alone so that the paper is cached before the others run in parallel.
            answers[todo[0]] = one(todo[0])
            answers.update(zip(todo[1:], pool.map(one, todo[1:]), strict=True))
            write_json(target, answers)
            failed = sum(answers[q] is None for q in todo)
            log.info("Saved %s (%d asked, %d failed)", target, len(todo), failed)


def table(out: Path, target: Path) -> None:
    """Combine the answer files in ``out`` into one CSV: one row per paper, one column per question."""
    rows = {path.stem: read_json(path) for path in sorted(out.glob("*.json"))}
    columns = list(dict.fromkeys(q for answers in rows.values() for q in answers))
    with target.open("w", newline="", encoding="utf-8-sig") as f:  # BOM so that Excel detects UTF-8
        writer = csv.writer(f)
        writer.writerow(["Paper", *columns])
        writer.writerows([name, *(answers.get(q) or "" for q in columns)] for name, answers in rows.items())
    log.info("Saved %s (%d papers, %d questions)", target, len(rows), len(columns))


def make_client(provider: str, model: str | None) -> Provider:
    if provider == "chatpdf":
        from .chatpdf import ChatPDF

        return ChatPDF(os.getenv("CHATPDF_KEY", ""))
    if provider == "claude":
        from .claude import DEFAULT_MODEL, Claude

        return Claude(os.getenv("ANTHROPIC_API_KEY"), model or DEFAULT_MODEL)
    from .ollama import Ollama

    return Ollama(model or os.getenv("OLLAMA_MODEL"))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="academia-maestro",
        description="Ask the same questions about many research papers and save the answers as JSON.",
    )
    parser.add_argument("--provider", choices=PROVIDERS, default="chatpdf", help="service to use (default: chatpdf)")
    parser.add_argument("--model", help="model for claude (default: claude-opus-5) or ollama (e.g. qwen3)")
    parser.add_argument("--papers", type=Path, default=Path("Reading"), help="folder with PDFs (default: Reading)")
    parser.add_argument("--out", type=Path, default=Path("Summary"), help="folder for the answers (default: Summary)")
    parser.add_argument(
        "--sources",
        type=Path,
        help="uploaded PDFs and their IDs (default: sources.json, sources-claude.json or sources-ollama.json)",
    )
    parser.add_argument(
        "--questions", type=Path, help="text file with one question per line (default: six general questions)"
    )
    parser.add_argument("--workers", type=int, help="questions asked in parallel (default: 4, ollama: 1)")
    parser.add_argument("--overwrite", action="store_true", help="ask again for papers that already have answers")
    parser.add_argument(
        "command",
        choices=["upload", "ask", "run", "table"],
        help="upload: send new PDFs; ask: save the answers; run: both; table: combine the answers into a CSV",
    )
    args = parser.parse_args(argv)
    if args.sources is None:
        args.sources = Path("sources.json" if args.provider == "chatpdf" else f"sources-{args.provider}.json")
    if args.workers is None:
        args.workers = 1 if args.provider == "ollama" else 4
    return args


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    if args.command == "table":
        table(args.out, args.out.with_suffix(".csv"))
        return
    load_dotenv(".env")
    load_dotenv(".env.local", override=True)
    try:
        client = make_client(args.provider, args.model)
    except ProviderError as e:
        raise SystemExit(str(e)) from None

    if args.command in ("upload", "run"):
        upload(client, args.papers, args.sources)
    if args.command in ("ask", "run"):
        sources = read_json(args.sources)
        if not sources:
            raise SystemExit(f"No uploaded papers in {args.sources}; run 'academia-maestro upload' first")
        questions = read_questions(args.questions) if args.questions else DEFAULT_QUESTIONS
        ask(client, sources, questions, args.out, args.overwrite, args.workers)


if __name__ == "__main__":
    main()
