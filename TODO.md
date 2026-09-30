# TODO

Open tasks. See also [Known issues](README.md#known-issues).

## 1. Modernise

- [x] Replace Poetry with uv and move the script into the package `src/academia_maestro`
- [x] Replace the hard-coded loop over papers 1 to 20 with `upload`, `ask` and `run` commands
- [x] Ask each question in its own request instead of parsing one long answer by keywords
- [x] Read questions from a text file; keep the 2024 federated learning questions as an example
- [x] Store source IDs in `sources.json` instead of `ids.txt`
- [x] Add tests with a fake client and Ruff
- [ ] Run once against the real ChatPDF API (costs requests)

## 2. Providers

- [x] Add Claude (Files API, prompt caching) and local models via Ollama
- [x] Ask questions in parallel, retry rate limits, re-ask only missing or failed answers
- [x] Add `table` to combine the answers into one CSV
- [ ] Run once against the Claude API (costs tokens)
- [ ] Run once against a local Ollama model

## 3. Publish

- [x] Add the MIT License
- [x] Replace the committed `.env` placeholder with `.env.example`
- [x] Check the files and the git history for secrets (only the placeholder `YOUR_CHATPDF_KEY` was committed)
- [x] Replace the old university e-mail address in the history
- [ ] Make the repository public
