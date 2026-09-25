<div align="center">

# Academia Maestro

**Ask the same questions about many research papers and collect the answers, using the ChatPDF API**

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)
![ChatPDF](https://img.shields.io/badge/ChatPDF-API-7C3AED)
![uv](https://img.shields.io/badge/uv-managed-DE5FE9?logo=uv&logoColor=white)
![Ruff](https://img.shields.io/badge/Ruff-D7FF64?logo=ruff&logoColor=black)
![License](https://img.shields.io/badge/License-MIT-yellow)

[Quick start](#quick-start) · [Usage](#usage) · [Questions](#questions) · [Development](#development)

</div>

Academia Maestro helps with literature reviews. It uploads the PDFs in a folder to [ChatPDF](https://www.chatpdf.com/),
asks each paper the same list of questions, and saves the answers as one JSON file per paper, so the papers can be
compared side by side.

## Features

- 📄 **Batch upload** of every PDF in a folder and its subfolders
- ❓ **Your own questions** from a plain text file, one per line
- 🗂️ **One JSON file per paper** with an answer for each question
- ♻️ **Resumable**: uploaded papers are remembered in `sources.json`, and papers with answers are skipped

> [!NOTE]
> Built in July 2024 for a literature review of federated learning surveys. Updated in 2026 to current dependencies,
> uv and Ruff.

> [!WARNING]
> The ChatPDF API is a paid service. Every upload and every question is one request; ten papers with six questions
> cost 70 requests.

## Contents

- [Quick start](#quick-start)
- [Usage](#usage)
- [Questions](#questions)
- [Output](#output)
- [Repository structure](#repository-structure)
- [Development](#development)
- [Known issues](#known-issues)
- [License](#license)
- [Author](#author)

## Quick start

Requirements: [uv](https://docs.astral.sh/uv/getting-started/installation/) and a
[ChatPDF API key](https://www.chatpdf.com/docs/api/backend).

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

3. Create the `.env` file and add your key as `CHATPDF_KEY`:

   ```bash
   cp .env.example .env
   ```

4. Put your PDFs into the folder `Reading/`, then upload them and ask the questions:

   ```bash
   uv run academia-maestro run
   ```

## Usage

```text
academia-maestro [--papers DIR] [--out DIR] [--sources FILE] [--questions FILE] [--overwrite] {upload,ask,run}
```

| Command | What it does |
|---|---|
| `upload` | Uploads each PDF that is not in `sources.json` yet and stores its ChatPDF source ID there |
| `ask` | Asks every question about every paper in `sources.json` and writes the answers to the output folder |
| `run` | `upload`, then `ask` |

| Option | Default | Meaning |
|---|---|---|
| `--papers` | `Reading` | Folder with the PDFs |
| `--out` | `Summary` | Folder for the JSON answers |
| `--sources` | `sources.json` | Uploaded PDFs and their source IDs |
| `--questions` | six general questions | Text file with your own questions |
| `--overwrite` | off | Ask again for papers that already have an answer file |

The key is read from `CHATPDF_KEY` in the environment, in `.env` or in `.env.local` (which wins).

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

`Summary/<paper>.json` maps each question to ChatPDF's answer, or to `null` if the request failed:

```json
{
  "What methodology did they use?": "The authors conducted a systematic literature review …",
  "What is the main contribution of the paper?": "…"
}
```

## Repository structure

| Path | Content |
|---|---|
| [`src/academia_maestro/cli.py`](src/academia_maestro/cli.py) | Command-line interface, upload and question loop |
| [`src/academia_maestro/chatpdf.py`](src/academia_maestro/chatpdf.py) | Small client for the ChatPDF API |
| [`questions/`](questions/) | Example question lists |
| [`tests/`](tests/) | Tests with a fake client; they do not call ChatPDF |

## Development

| Task | Command |
|---|---|
| Run the tests | `uv run pytest` |
| Lint | `uv run ruff check .` |
| Format | `uv run ruff format .` |

## Known issues

- ChatPDF limits a conversation to about 2,500 tokens; very long questions are cut off.
- The tests use a fake client. The 2026 version has not been run against the real API, to avoid costs.
- Uploaded PDFs stay in your ChatPDF account until you delete them there.

## License

The code is licensed under the [MIT License](LICENSE). Papers you upload keep their own copyright; they are not part
of this repository.

## Author

Nicolas Huber · [GitHub](https://github.com/HuberNicolas) · nicolas.huber.dev@gmail.com
