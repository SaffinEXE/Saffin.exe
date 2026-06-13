# Changelog

## [Unreleased] — feat/local-ai-assistant

### Added
- **Local AI assistant** (`scripts/assistant.py`)
  - Ollama-powered interactive chat with streaming responses
  - Tool calling: log sessions, add ideas, score decisions, generate reviews
  - `STREAKS` tool: current/longest consecutive-day tracking
  - `SEARCH_REVIEWS` tool: TF-IDF search over weekly review files
  - First-run setup check for missing Ollama or model
  - CLI flags: `--model`, `--host`, `--no-stream`
  - Non-interactive mode: `log`, `status`, `idea`, `streaks`, `search_reviews`, `ask`
  - Conversation history persistence (`.saffin_chat_history.json`)
  - Fallback rule-based mode when Ollama is unavailable
- **RAG indexer** (`scripts/rag.py`)
  - Chunks markdown files by section heading
  - Builds TF-IDF index via scikit-learn
  - Auto-caches to `.cache/weekly_reviews_index.pkl`
  - CLI: `--build` to rebuild, positional arg to query
- **Scheduling scripts**
  - `scripts/check_reminders.sh` (Linux/macOS cron)
  - `scripts/check_reminders.ps1` (Windows Task Scheduler)
- **CLI integration** — `chat` subcommand added to `saffin.py`
- **Tests**
  - `tests/test_assistant.py` — 12 smoke tests
  - `tests/test_rag.py` — RAG build + search tests

### Changed
- `requirements.txt` — added `requests`, `scikit-learn`, `numpy`
- `.gitignore` — added `.cache/`, `.saffin_chat_history.json`
- `README.md` — documented assistant, streaks, and RAG usage
