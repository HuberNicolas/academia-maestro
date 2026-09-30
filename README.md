<div align="center">

# Academia Maestro

**Ask the same questions about many research papers and get a comparison table for your literature review**

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)
![ChatPDF](https://img.shields.io/badge/ChatPDF-API-7C3AED)
![Claude](https://img.shields.io/badge/Claude-API-D97757?logo=anthropic&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-local-000000?logo=ollama&logoColor=white)
![uv](https://img.shields.io/badge/uv-managed-DE5FE9?logo=uv&logoColor=white)
![Ruff](https://img.shields.io/badge/Ruff-D7FF64?logo=ruff&logoColor=black)
![License](https://img.shields.io/badge/License-MIT-yellow)

[Quick start](#quick-start) · [Literature review](#systematic-literature-review) · [Providers](#providers) · [Usage](#usage) · [Development](#development)

</div>

Academia Maestro helps with systematic literature reviews. It sends the PDFs in a folder to a language model, asks
each paper the same list of questions and saves the answers as one JSON file per paper. `table` then combines them
into one CSV: one row per paper, one column per question. That is the comparison table a literature review needs to
show what existing work covers and where the research gap is.

## Features

- 📄 **Batch processing** of every PDF in a folder and its subfolders
- 🤖 **Three providers**: [ChatPDF](https://www.chatpdf.com/), [Claude](https://www.anthropic.com/api) or a local model with [Ollama](https://ollama.com/)
- ❓ **Your own questions** from a plain text file, one per line
- 📊 **Comparison table** as CSV for Excel, Numbers or LaTeX
- ♻️ **Resumable**: uploaded papers are remembered, and only new or failed questions are asked again
- ⚡ **Fast**: questions about a paper run in parallel; rate limits and server errors are retried

> [!NOTE]
> Built in July 2024 for a literature review of federated learning surveys. Updated in 2026 to current dependencies,
> uv and Ruff, with Claude and Ollama as further providers.

> [!WARNING]
> ChatPDF and Claude are paid services. With ChatPDF, every upload and every question is one request; ten papers with
> six questions cost 70 requests. With Claude you pay per token; the paper is cached, so further questions about the
> same paper cost about a tenth of the first. Ollama runs on your own machine and costs nothing.

## Contents

- [Quick start](#quick-start)
- [Systematic literature review](#systematic-literature-review)
- [Providers](#providers)
- [Usage](#usage)
- [Questions](#questions)
- [Output](#output)
- [Repository structure](#repository-structure)
- [Development](#development)
- [Known issues](#known-issues)
- [License](#license)
- [Author](#author)

## Quick start

Requirements: [uv](https://docs.astral.sh/uv/getting-started/installation/) and one of: a
[ChatPDF API key](https://www.chatpdf.com/docs/api/backend), a [Claude API key](https://platform.claude.com/) or
[Ollama](https://ollama.com/download) with a model.

1. Clone the repository:

   ```bash
   git clone git@github.com:HuberNicolas/academia-maestro.git
   ```

   ```bash
   cd academia-maestro
   ```

2. Install the dependencies:

   ```bash
   uv sync
   ```

3. Create the `.env` file and add the key of your provider:

   ```bash
   cp .env.example .env
   ```

4. Put your PDFs into the folder `Reading/`, then upload them and ask the questions:

   ```bash
   uv run academia-maestro run
   ```

5. Combine the answers into `Summary.csv`:

   ```bash
   uv run academia-maestro table
   ```

## Systematic literature review

A typical workflow, for example for a review following [PRISMA](https://www.prisma-statement.org/):

1. **Collect** the papers that passed your screening in `Reading/`.
2. **Write the questions** that make up the columns of your comparison table, one per line, for example:

   ```text
   Which data set does the paper use?
   Is the approach evaluated on real devices or only in simulation?
   Does the paper address privacy attacks? Answer with yes, no or partly, then one sentence.
   What future work do the authors name?
   ```

   Closed questions ("Answer with yes, no or partly") give short cells that are easy to compare; open questions give
   material for the text.

3. **Run** `academia-maestro --questions my-questions.txt run`, then `academia-maestro table`.
4. **Open** `Summary.csv` in a spreadsheet, check every cell against the paper and shorten it.
5. **Find the gap**: columns where most papers answer "no" or "not addressed" show what existing work does not
   cover. The table is the evidence for that claim in your thesis or paper.

If you add a question later, run `ask` again: only the new question is asked, existing answers are kept.

> [!IMPORTANT]
> Language models make mistakes. Use the answers as a first draft and check them against the papers before you cite
> them.

## Providers

| Provider | `--provider` | Key | Reads the PDF | Default model |
|---|---|---|---|---|
| ChatPDF | `chatpdf` (default) | `CHATPDF_KEY` | Text, on ChatPDF's servers | fixed by ChatPDF |
| Claude | `claude` | `ANTHROPIC_API_KEY` | Text, figures and tables, via the Files API | `claude-opus-5` |
| Ollama | `ollama` | none | Text only, extracted locally with pypdf | none, set `--model` |

```bash
uv run academia-maestro --provider claude run
```

```bash
uv run academia-maestro --provider ollama --model qwen3 run
```

- **Claude** uploads each PDF once with the Files API and caches it, so each further question only pays for the
  question and the answer. Choose a cheaper model with `--model claude-sonnet-5`. Instead of `ANTHROPIC_API_KEY`,
  a login with `ant auth login` works too.
- **Ollama** keeps the papers on your machine, which helps with unpublished or confidential papers. Pull a model with
  a large context first (`ollama pull qwen3`); the paper is sent with a context of 32,768 tokens. Set `OLLAMA_HOST`
  if Ollama does not run on `localhost:11434`. Questions are asked one after the other, so Ollama can reuse the
  processed paper.

Each provider keeps its uploaded papers in its own file (`sources.json`, `sources-claude.json`,
`sources-ollama.json`). To compare providers, give each its own output folder with `--out`.

## Usage

```text
academia-maestro [--provider {chatpdf,claude,ollama}] [--model MODEL] [--papers DIR] [--out DIR]
                 [--sources FILE] [--questions FILE] [--workers N] [--overwrite] {upload,ask,run,table}
```

| Command | What it does |
|---|---|
| `upload` | Uploads each PDF that is not in the sources file yet and stores its ID there |
| `ask` | Asks every question about every uploaded paper and writes the answers to the output folder |
| `run` | `upload`, then `ask` |
| `table` | Combines the answers in the output folder into `<out>.csv`, e.g. `Summary.csv` |

| Option | Default | Meaning |
|---|---|---|
| `--provider` | `chatpdf` | `chatpdf`, `claude` or `ollama` |
| `--model` | see [Providers](#providers) | Model for Claude or Ollama |
| `--papers` | `Reading` | Folder with the PDFs |
| `--out` | `Summary` | Folder for the JSON answers |
| `--sources` | `sources.json` or `sources-<provider>.json` | Uploaded PDFs and their IDs |
| `--questions` | six general questions | Text file with your own questions |
| `--workers` | 4, Ollama: 1 | Questions asked in parallel |
| `--overwrite` | off | Ask all questions again, even those with an answer |

Keys are read from the environment, from `.env` or from `.env.local` (which wins).

## Questions

Without `--questions`, each paper gets six general questions: a summary, the problem, the methodology, the main
contribution, the limitations and why the paper is still valuable. For your own questions, write a text file with
one question per line; lines starting with `#` are ignored. [`questions/federated-learning.txt`](questions/federated-learning.txt)
holds the questions used for the 2024 review:

```bash
uv run academia-maestro --questions questions/federated-learning.txt ask
```

Each question is sent as its own request, so the answers do not depend on each other.

## Output

`Summary/<paper>.json` maps each question to the answer, or to `null` if the request failed:

```json
{
  "What methodology did they use?": "The authors conducted a systematic literature review …",
  "What is the main contribution of the paper?": "…"
}
```

`table` turns these files into `Summary.csv`:

| Paper | What methodology did they use? | What is the main contribution of the paper? |
|---|---|---|
| smith-2023 | Systematic literature review of 120 papers … | A taxonomy of … |
| wang-2024 | Experiments on three benchmark data sets … | … |

The CSV is UTF-8 with a byte order mark, so Excel shows umlauts and accents correctly.

## Repository structure

| Path | Content |
|---|---|
| [`src/academia_maestro/cli.py`](src/academia_maestro/cli.py) | Command-line interface, upload, question loop and CSV table |
| [`src/academia_maestro/provider.py`](src/academia_maestro/provider.py) | Interface that every provider implements |
| [`src/academia_maestro/chatpdf.py`](src/academia_maestro/chatpdf.py) | Client for the ChatPDF API |
| [`src/academia_maestro/claude.py`](src/academia_maestro/claude.py) | Client for the Claude API |
| [`src/academia_maestro/ollama.py`](src/academia_maestro/ollama.py) | Client for a local Ollama server |
| [`questions/`](questions/) | Example question lists |
| [`tests/`](tests/) | Tests with fake clients; they call no API |

## Development

| Task | Command |
|---|---|
| Run the tests | `uv run pytest` |
| Lint | `uv run ruff check .` |
| Format | `uv run ruff format .` |

## Known issues

- ChatPDF limits a conversation to about 2,500 tokens; very long questions are cut off.
- Ollama only sees the text of a PDF. Scanned PDFs without a text layer are skipped; figures and tables are lost.
- The tests use fake clients. The 2026 version has not been run against the real APIs yet, to avoid costs.
- Uploaded PDFs stay in your ChatPDF account or Claude workspace until you delete them there.

## License

The code is licensed under the [MIT License](LICENSE). Papers you upload keep their own copyright; they are not part
of this repository.

## Author

Nicolas Huber · [GitHub](https://github.com/HuberNicolas) · nicolas.huber.dev@gmail.com
