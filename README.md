# Saffin OS v2 — Setup & Usage

## Folder Contents
```
Saffin_OS_v2/
├── Saffin_OS_v2.md          # Main rulebook/policy
├── idea_vault.md            # Local markdown idea backlog
├── idea_vault_sheets.csv     # Importable CSV for Google Sheets (with formulas)
├── journal/
│   └── journal.csv          # Daily log (date, primary_minutes, secondary_minutes, notes)
├── weekly_reviews/
│   └── TEMPLATE.md           # Copy this each week as YYYY-MM-DD.md
└── scripts/
    └── decision_score.py     # Decision Framework calculator
```

## Quick Start

### 1. Daily logging
Open `journal/journal.csv` and add a row each day:
```
2026-06-13,30,20,"Wrote unit tests for X; 20 min cardio"
```

### 2. Weekly review
Copy `weekly_reviews/TEMPLATE.md` to `weekly_reviews/2026-06-14.md`, fill it in.

### 3. New idea
Copy the template block in `idea_vault.md`, fill in date/description, wait 48h, then score.

### 4. Decision Framework script
Interactive:
```
python scripts/decision_score.py
```
Direct (impact, alignment, effort, risk, opportunity_cost):
```
python scripts/decision_score.py 4 4 2 2 3
```

### 5. Google Sheets version
Import `idea_vault_sheets.csv` into Google Sheets (File → Import → Replace/Append).
The Score and Action columns already contain formulas — they'll auto-fill as you
add new rows if you copy the formula down.

## Automation CLI (`scripts/saffin.py`)

A single command-line tool that handles journaling, idea scoring, and weekly reviews.

### Log a daily entry
```
python scripts/saffin.py log <primary_minutes> <secondary_minutes> --notes "what you did"
```
Example:
```
python scripts/saffin.py log 30 20 --notes "Wrote unit tests; 20 min cardio"
```
Appends a row to `journal/journal.csv` (defaults to today's date; use `--date YYYY-MM-DD` to backfill).

### Add an idea
```
python scripts/saffin.py idea "Idea title" --description "short description"
```
Adds a new entry to `idea_vault.md` with the current timestamp. It becomes eligible for scoring after 48 hours.

### Score pending ideas
```
python scripts/saffin.py score
```
Scans `idea_vault.md` for unscored ideas that are 48h+ old, prompts you for Impact/Alignment/Effort/Risk/Opportunity Cost (1-5 each), computes the score via `decision_score.py`, and writes the result + Act/Vault/Drop back into the file.

### Generate weekly review
```
python scripts/saffin.py review
```
Creates `weekly_reviews/YYYY-MM-DD.md` (named for the end of the current week) pre-filled with your Primary/Secondary session counts pulled from `journal/journal.csv`. Use `--force` to overwrite an existing file.

### Check status / reminders
```
python scripts/saffin.py status
```
Shows this week's session counts, how many ideas are pending/ready for scoring, and reminds you to run the weekly review on Sundays.

### Suggested daily/weekly habit
- Each evening: `python scripts/saffin.py log <p> <s> --notes "..."`
- Anytime: `python scripts/saffin.py status` to check progress
- Sunday: `python scripts/saffin.py review` then `python scripts/saffin.py score`


- Put this whole folder in a Git repo (or Google Drive) for sync/backup.
- Optional: add a weekly calendar reminder (Sunday) to do the 15-min review.

## Running tests

Install pytest (recommended into a virtual environment) and run the test suite:

```powershell
python -m pip install -r requirements.txt
pytest -q
```

CI: A GitHub Actions workflow is included at `.github/workflows/ci.yml` to run tests on push and pull requests.

## Developer commands

Common tasks with `make` (on Windows use WSL or run the commands directly):

```powershell
make install   # install dependencies
make test      # run pytest
make package   # install package in editable mode
```

Or install the package locally and use console scripts:

```powershell
python -m pip install -e .
saffin status
decision-score 4 4 2 2 3
```

## Linting and pre-commit

Install development tools:

```powershell
python -m pip install -r dev-requirements.txt
```

Enable pre-commit hooks locally:

```powershell
pre-commit install
pre-commit run --all-files
```

To run the linter manually:

```powershell
ruff check .
black --check .
```

## Local assistant (LLM + tools)

📖 **Full guide:** [docs/ASSISTANT.md](docs/ASSISTANT.md)

A starter assistant script is included at `scripts/assistant.py`. It uses a local LLM (Ollama) when available and falls back to a simple rule-based responder.

Requirements:
- Ollama (install and pull a model) — see https://ollama.com

Run the assistant:

```powershell
cd scripts
python assistant.py
```

The assistant supports: logging sessions, adding ideas, scoring ideas (interactive), and generating weekly reviews.

## Streak tracking

The assistant can track your daily logging streaks.

### What it measures
- **Current streak** — consecutive days ending today (or yesterday)
- **Longest streak** — best run ever
- **Total days** — distinct dates you've logged

### Usage

Chat:
```
You: How's my streak?
Saffin: 🔥 Current streak: 5 day(s)
    🏆 Longest streak: 12 day(s)
    📅 Total days logged: 47
    📝 Last logged: 2025-01-15
    ✅ You're logged in today — keep the streak alive!
```

CLI:
```powershell
python scripts/assistant.py streaks
```

Cron bonus — streak reminders:
Add to `scripts/check_reminders.sh`:
```bash
$PYTHON "$BASE_DIR/scripts/assistant.py" streaks
```

## Releasing and versioning

This project uses Git tags and a GitHub Actions workflow to create releases. Tag a new release locally and push the tag:

```powershell
git tag v0.1.0
git push origin v0.1.0
```

Pushing a `v*` tag triggers `.github/workflows/release.yml`, which will build distribution archives and create a GitHub Release. To publish to PyPI, set the secret `PYPI_API_TOKEN` in the repository settings.

If you want me to create a branch and open a PR for these changes, provide the repository remote URL and grant push access (or push the branch yourself). I cannot push or create a PR without remote permissions.
