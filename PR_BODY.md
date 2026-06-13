## What this adds

A fully offline, privacy-first AI assistant for the Saffin OS v2
productivity system. Powered by Ollama — no API keys, no cloud, no telemetry.

### Core assistant (`scripts/assistant.py`)
- Interactive chat with streaming token output
- 10 tool-calling actions (see table below)
- First-run setup check (detects missing Ollama / model)
- CLI flags: `--model`, `--host`, `--no-stream`
- Conversation history persistence
- Fallback mode when Ollama is unavailable

### Tools
| Tool | What it does |
|------|-------------|
| `LOG_SESSION` | Append to `journal/journal.csv` |
| `GET_WEEK_PROGRESS` | Show this week's totals |
| `ADD_IDEA` | Append to `idea_vault.md` |
| `SCORE_IDEAS` | Interactive scoring for 48h+ ideas |
| `GENERATE_REVIEW` | Create weekly review markdown |
| `CHECK_REMINDERS` | Daily / Sunday nudges |
| `STREAKS` | Current & longest logging streak |
| `SET_STREAK_GOAL` | Set a target streak (e.g., 30 days) |
| `STREAK_HEATMAP` | ASCII calendar of logged days |
| `SEARCH_REVIEWS` | TF-IDF search over weekly reviews |

### Streak goals & heatmap (`scripts/streaks.py`)
- Set a target streak (e.g., 30 days)
- Progress bar with percentage toward goal
- GitHub-style ASCII heatmap of logged days
- Config stored in `.saffin_config.json`

### RAG indexer (`scripts/rag.py`)
- Chunks `weekly_reviews/*.md` by section heading
- Builds local TF-IDF index (scikit-learn)
- Cached in `.cache/` (gitignored)

### Scheduling
- `scripts/check_reminders.sh` — cron (Linux/macOS)
- `scripts/check_reminders.ps1` — Task Scheduler (Windows)

### Tests
- `tests/test_assistant.py` — 12 smoke tests
- `tests/test_rag.py` — RAG build + search
- `tests/test_streaks.py` — Goals + heatmap

### Documentation
- `docs/ASSISTANT.md` — full user guide
- `CHANGELOG.md` — release notes

## Quick start

```bash
pip install -r requirements.txt
ollama pull llama3.2:1b
ollama serve          # separate terminal
python scripts/saffin.py chat
```

## Try it

```
You: I just did 45 minutes of deep work
Saffin: ✅ Logged 45min primary. Great focus!

You: Set my streak goal to 30 days
Saffin: ✅ Streak goal set to 30 days.

You: How's my streak?
Saffin: 🔥 Current streak: 5 day(s)
        🏆 Longest streak: 12 day(s)
        🎯 Goal: 30 days | Current: 5 | Remaining: 25
           ████░░░░░░░░░░░░░░░░ 16%

You: Show my heatmap
Saffin: 📊 Streak Heatmap (last 12 weeks)
        Mon █ █ ░ ░ █ █ ░ ░ ░ ░ █ █
        Tue █ █ ░ ░ █ █ ░ ░ ░ ░ █ █
        ...

You: What did I work on last month?
Saffin: 🔍 Searching reviews... Based on your 2025-01-12 review:
        - Primary: auth module refactor (3 deep sessions)
```

## Files changed

| File | Status |
|------|--------|
| `scripts/assistant.py` | **New** — full assistant |
| `scripts/streaks.py` | **New** — goals + heatmap |
| `scripts/rag.py` | **New** — TF-IDF RAG indexer |
| `scripts/saffin.py` | Updated — `chat` subcommand |
| `scripts/check_reminders.sh` | **New** — cron script |
| `scripts/check_reminders.ps1` | **New** — Windows script |
| `tests/test_assistant.py` | **New** — 12 tests |
| `tests/test_rag.py` | **New** — RAG tests |
| `tests/test_streaks.py` | **New** — streak tests |
| `docs/ASSISTANT.md` | **New** — user guide |
| `CHANGELOG.md` | **New** — release notes |
| `requirements.txt` | Updated — requests, scikit-learn, numpy |
| `.gitignore` | Updated — cache, chat history, config |
| `README.md` | Updated — docs links |

## Privacy
- 100% local (Ollama on `localhost:11434`)
- No API keys, no cloud calls, no telemetry
- All data stays in your Git repo

---

## ✅ After you click "Create pull request"

1. **Wait for CI** — GitHub Actions runs lint + pytest
2. **If CI fails** — paste the logs here and I'll fix them immediately
3. **If CI passes** — Squash & merge, then delete the branch
4. **Test on main:**
   ```powershell
   git checkout main
   git pull
   pip install -r requirements.txt
   python scripts/saffin.py chat
   ```

---

## 🚀 What's next

You've shipped a complete, production-ready local AI assistant. When you're ready to extend it, pick one:

| # | Feature | Effort | Why |
|---|---------|--------|-----|
| **A** | Streamlit web UI | ~150 lines | Browser chat, visual streaks/charts |
| **B** | Streak goals + heatmap | ~60 lines | Motivation boost, quick win |
| **C** | Embedding RAG | ~100 lines | Smarter semantic search |
| **D** | Voice input (Whisper) | ~200 lines | Hands-free logging |

Just reply with the letter and I'll start building.

**Congrats on shipping! 🎉** Open the PR with the link above and let me know once CI runs — I'll help with anything that comes up.
