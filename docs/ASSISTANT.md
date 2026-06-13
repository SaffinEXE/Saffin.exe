# Saffin AI Assistant — User Guide

A fully offline, privacy-first AI assistant for Saffin OS v2. Powered by Ollama.

## Quick Start

1. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

2. Install Ollama & pull a model:
   ```bash
   # https://ollama.com/download
   ollama pull llama3.2:1b
   ollama serve   # keep running in background
   ```

3. Start the assistant:
   ```powershell
   python scripts/saffin.py chat
   # or
   python scripts/assistant.py
   ```

## Modes

| Mode | Command | Use case |
|------|---------|----------|
| Interactive chat | `python scripts/assistant.py` | Daily workflow, natural language |
| CLI subcommands | `python scripts/assistant.py log 30 10 "deep work"` | Scripting, cron, quick actions |
| Non-interactive ask | `python scripts/assistant.py ask "How's my week?"` | One-off queries |

## Available Tools

The assistant can call these tools automatically during chat:

| Tool | Purpose |
|------|---------|
| `LOG_SESSION(p, s, notes)` | Append to `journal/journal.csv` |
| `GET_WEEK_PROGRESS()` | Show this week's primary/secondary totals |
| `ADD_IDEA(title, desc)` | Add to `idea_vault.md` (48h cooldown before scoring) |
| `SCORE_IDEAS()` | Interactive scoring for eligible ideas |
| `GENERATE_REVIEW()` | Create weekly review markdown |
| `CHECK_REMINDERS()` | Daily log + Sunday review nudges |
| `STREAKS()` | Current & longest consecutive-day logging streak |
| `SEARCH_REVIEWS(query)` | TF-IDF search over `weekly_reviews/*.md` |

## CLI Flags

```powershell
python scripts/assistant.py --model mistral
python scripts/assistant.py --host http://localhost:11434
python scripts/assistant.py --no-stream
```

## RAG Search

- Index builds automatically on first `SEARCH_REVIEWS` call.
- Manual rebuild: `python scripts/rag.py --build`
- Cache location: `.cache/weekly_reviews_index.pkl` (gitignored)

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `❌ Cannot reach Ollama` | Run `ollama serve` in another terminal |
| `⚠️ Model not found` | Run `ollama pull llama3.2:1b` (or your chosen model) |
| Streaming looks broken | Use `--no-stream` or update Ollama (`ollama update`) |
| Tools not triggering | Ensure prompts are clear: "Log 30 min primary work" |
| RAG returns nothing | Add at least one `.md` to `weekly_reviews/` and rebuild |

## Privacy & Data

- ✅ 100% local (Ollama runs on `localhost:11434`)
- ✅ No API keys, no cloud calls, no telemetry
- ✅ Chat history saved to `.saffin_chat_history.json` (gitignored)
- ✅ All productivity data stays in your Git repo

## Scheduling Reminders

**Linux/macOS (cron):**
```bash
crontab -e
# Add: 0 20 * * * /path/to/Saffin_OS_v2/scripts/check_reminders.sh
```

**Windows (Task Scheduler):**
- Action: `powershell.exe`
- Arguments: `-ExecutionPolicy Bypass -File "C:\path\to\scripts\check_reminders.ps1"`
- Trigger: Daily at 20:00
