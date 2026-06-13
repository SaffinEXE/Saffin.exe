#!/usr/bin/env python3
"""
Saffin Assistant v1.0
A local AI chatbot for the Saffin OS v2 productivity system.

Runs entirely offline using Ollama's HTTP API (or falls back to a rule-based assistant).
"""

import subprocess
import json
import sys
import re
from pathlib import Path
from datetime import date, datetime, timedelta
from typing import Optional, Dict, List, Any
import requests
import os
import argparse
from dataclasses import dataclass

# ============================================================================
# CONFIG
# ============================================================================
BASE_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = BASE_DIR / "scripts"
JOURNAL_CSV = BASE_DIR / "journal" / "journal.csv"
IDEA_VAULT_MD = BASE_DIR / "idea_vault.md"
WEEKLY_REVIEWS_DIR = BASE_DIR / "weekly_reviews"
CHAT_HISTORY_FILE = BASE_DIR / ".saffin_chat_history.json"

# Ollama config
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
MODEL = os.environ.get("SAFFIN_MODEL", "llama3.2:1b")


@dataclass
class Config:
    model: str = MODEL
    host: str = OLLAMA_HOST
    stream: bool = True


CONFIG = Config()

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def call_ollama(
    messages: List[Dict[str, str]],
    stream: Optional[bool] = None,
    model: Optional[str] = None,
    host: Optional[str] = None,
) -> str:
    """
    Call the local Ollama API.
    If stream is True, print tokens as they arrive and return the full response.
    """
    model = model or CONFIG.model
    host = host or CONFIG.host
    if stream is None:
        stream = CONFIG.stream

    try:
        response = requests.post(
            f"{host}/api/chat",
            json={
                "model": model,
                "messages": messages,
                "stream": stream,
            },
            stream=stream,
            timeout=120,
        )
        response.raise_for_status()

        if not stream:
            # Non-streaming: return full content
            data = response.json()
            return data.get("message", {}).get("content", "")

        # Streaming mode: print tokens as they arrive
        full_response = ""
        print("Saffin: ", end="", flush=True)
        for line in response.iter_lines():
            if not line:
                continue
            try:
                chunk = json.loads(line.decode("utf-8"))
                token = chunk.get("message", {}).get("content", "")
                if token:
                    print(token, end="", flush=True)
                    full_response += token
                if chunk.get("done"):
                    break
            except json.JSONDecodeError:
                # ignore non-json lines
                continue
        print()
        return full_response

    except requests.exceptions.ConnectionError:
        return "❌ Cannot reach Ollama. Run: `ollama serve`"
    except Exception as e:
        return f"❌ Error: {e}"


def check_setup() -> bool:
    """Verify Ollama is running and the requested model is available.

    Returns True if the environment looks ready for the LLM, False otherwise.
    """
    try:
        # Check service
        resp = requests.get(f"{OLLAMA_HOST}/api/models", timeout=3)
        resp.raise_for_status()
        data = resp.json()
        # `data` is typically a list of model objects; fall back to string search
        names = []
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    names.append(item.get("name") or item.get("id") or "")
                else:
                    names.append(str(item))
        else:
            names.append(str(data))

        if any(MODEL in n for n in names):
            return True
        print(f"⚠️ Model '{MODEL}' not found on Ollama. Run: ollama pull {MODEL}")
        return False
    except Exception:
        print(
            "⚠️ Ollama is not reachable. Install and run Ollama "
            "(https://ollama.com/download) and then `ollama serve`."
        )
        return False


def save_chat_history(messages: List[Dict[str, str]]):
    """Save conversation to disk for persistence."""
    with open(CHAT_HISTORY_FILE, "w") as f:
        json.dump(messages, f, indent=2)


def load_chat_history() -> List[Dict[str, str]]:
    """Load previous conversation."""
    if CHAT_HISTORY_FILE.exists():
        with open(CHAT_HISTORY_FILE, "r") as f:
            return json.load(f)
    return []

# ============================================================================
# SAFFIN TOOLS (Functions the assistant can call)
# ============================================================================


def log_session(primary_minutes: int, secondary_minutes: int, notes: str) -> str:
    """Log a work session."""
    try:
        cmd = [
            sys.executable, str(SCRIPTS_DIR / "saffin.py"), "log",
            str(primary_minutes), str(secondary_minutes),
            "--notes", notes
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return (
                f"✅ Logged {primary_minutes}min primary + "
                f"{secondary_minutes}min secondary.\nNotes: {notes}"
            )
        else:
            return f"⚠️ Logging failed: {result.stderr}"
    except Exception as e:
        return f"❌ Error: {e}"


def get_week_progress() -> str:
    """Get this week's totals."""
    try:
        cmd = [sys.executable, str(SCRIPTS_DIR / "saffin.py"), "status"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return (
            result.stdout
            if result.returncode == 0
            else f"⚠️ Status check failed: {result.stderr}"
        )
    except Exception as e:
        return f"❌ Error: {e}"


def add_idea(title: str, description: str) -> str:
    """Add a new idea to the vault."""
    try:
        cmd = [
            sys.executable, str(SCRIPTS_DIR / "saffin.py"), "idea",
            title,
            "--description", description
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return (
            f"✅ Idea added: **{title}**\nWait 48 hours before scoring."
            if result.returncode == 0
            else f"⚠️ Failed: {result.stderr}"
        )
    except Exception as e:
        return f"❌ Error: {e}"


def score_ideas() -> str:
    """Start interactive idea scoring."""
    return "⏳ Starting idea scoring (interactive)...\n[Running in terminal]"


def generate_review() -> str:
    """Generate weekly review."""
    try:
        cmd = [sys.executable, str(SCRIPTS_DIR / "saffin.py"), "review"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return (
            f"✅ Weekly review generated.\n{result.stdout}"
            if result.returncode == 0
            else f"⚠️ Failed: {result.stderr}"
        )
    except Exception as e:
        return f"❌ Error: {e}"


def check_reminders() -> str:
    """Check if reminders are due (Sunday = review day)."""
    today = date.today()
    day_name = today.strftime("%A")

    reminders = []
    if day_name == "Sunday":
        reminders.append("📋 It's Sunday! Time for your weekly review.")

    # Check if journal has entry today
    try:
        with open(JOURNAL_CSV, "r") as f:
            content = f.read()
            if str(today) not in content:
                reminders.append(
                    "📝 You haven't logged today yet. "
                    "Time to record your session!"
                )
    except:
        pass

    if reminders:
        return "\n".join(reminders)
    else:
        return "✅ You're all caught up!"


def calculate_streaks() -> Dict[str, Any]:
    """
    Calculate current and longest logging streaks from journal.csv.
    A "logged day" is any row in journal.csv.
    Returns dict with:
      - current_streak: consecutive days ending today (or yesterday if no entry today)
      - longest_streak: longest run of consecutive days ever
      - total_days: total number of distinct logged days
      - last_logged: ISO date of most recent entry (or None)
      - is_on_streak: True if user logged today
    """
    if not JOURNAL_CSV.exists():
        return {
            "current_streak": 0,
            "longest_streak": 0,
            "total_days": 0,
            "last_logged": None,
            "is_on_streak": False,
        }

    # Read dates from CSV (skip header if present)
    dates = set()
    with open(JOURNAL_CSV, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            if i == 0 and line.lower().startswith("date"):
                continue
            # Parse first field as date
            first_field = line.split(",")[0].strip()
            try:
                dates.add(date.fromisoformat(first_field))
            except ValueError:
                continue

    if not dates:
        return {
            "current_streak": 0,
            "longest_streak": 0,
            "total_days": 0,
            "last_logged": None,
            "is_on_streak": False,
        }

    sorted_dates = sorted(dates)
    today = date.today()
    last_logged = sorted_dates[-1]
    is_on_streak_today = last_logged == today

    # Current streak: walk backwards from the most recent date
    current_streak = 0
    cursor = last_logged
    while cursor in dates:
        current_streak += 1
        cursor = cursor - timedelta(days=1)

    # If last log is older than yesterday, current streak is broken
    if (today - last_logged).days > 1:
        current_streak = 0

    # Longest streak: scan all sorted dates
    longest_streak = 1
    run = 1
    for i in range(1, len(sorted_dates)):
        if (sorted_dates[i] - sorted_dates[i - 1]).days == 1:
            run += 1
            longest_streak = max(longest_streak, run)
        else:
            run = 1

    return {
        "current_streak": current_streak,
        "longest_streak": max(longest_streak, current_streak),
        "total_days": len(dates),
        "last_logged": sorted_dates[-1].isoformat(),
        "is_on_streak": is_on_streak_today,
    }


def streaks() -> str:
    """
    Human-readable streaks string. LLM-callable wrapper.
    """
    # Prefer using the standalone `scripts/streaks.py` module if available
    try:
        from scripts import streaks as _streaks
        return _streaks.streaks_summary()
    except Exception:
        # Fallback to built-in calculation
        s = calculate_streaks()
        if s["total_days"] == 0:
            return "📊 No sessions logged yet. Log your first one to start a streak!"

        parts = [
            f"🔥 Current streak: **{s['current_streak']} day(s)**",
            f"🏆 Longest streak: **{s['longest_streak']} day(s)**",
            f"📅 Total days logged: {s['total_days']}",
            f"📝 Last logged: {s['last_logged']}",
        ]
        if s["is_on_streak"]:
            parts.append("✅ You're logged in today — keep the streak alive!")
        else:
            parts.append("💡 Tip: log today to start a new streak.")

        return "\n".join(parts)

# ============================================================================
# TOOL DEFINITIONS FOR THE LLM
# ============================================================================

TOOLS_PROMPT = """
You have access to the following tools to help manage Saffin OS:

1. **LOG_SESSION(primary_minutes, secondary_minutes, notes)**
   - Example: LOG_SESSION(45, 15, "Wrote tests; checked email")
   - Use when user finishes a work session.

2. **GET_WEEK_PROGRESS()**
   - Shows current week's primary/secondary totals.
   - Use when user asks "how much have I worked?" or "progress".

3. **ADD_IDEA(title, description)**
   - Example: ADD_IDEA("Blog series", "5-part guide on productivity")
   - Use when user wants to capture an idea.

4. **SCORE_IDEAS()**
   - Starts interactive scoring for 48h+ old ideas.
   - Use when user is ready to evaluate ideas.

5. **GENERATE_REVIEW()**
   - Creates the weekly review file.
   - Use when user says "review" or on Sundays.

6. **CHECK_REMINDERS()**
   - Checks what's due today (logs, reviews, etc.)
   - Use proactively on startup.

7. **STREAKS()**
    - Returns current consecutive-day logging streak and the longest streak ever.
    - Use when the user asks "how's my streak?", "am I on a streak?", or wants motivation.

9. **SET_STREAK_GOAL(days)**
   - Set a target streak goal (e.g., 30 days).
   - Use when user says "set my goal to 30 days" or "I want a 60-day streak".

10. **STREAK_HEATMAP()**
    - Show a visual calendar heatmap of logged days.
    - Use when user asks "show my heatmap", "show my calendar", or wants a visual.

8. **SEARCH_REVIEWS(query)**
    - Search past `weekly_reviews/*.md` for relevant passages and return the top matches.
    - Example: SEARCH_REVIEWS("what did I work on last month?")

When you decide to call a tool, format it EXACTLY like this on a new line:
TOOL: TOOL_NAME(arg1, arg2, ...)

Example:
User: I just did 30 min of deep work
You: Great! Let me log that.
TOOL: LOG_SESSION(30, 0, "Deep work session")

After the tool runs, you'll get the result and should acknowledge it naturally.
"""

SYSTEM_PROMPT = f"""You are Saffin, a warm and encouraging AI assistant for the Saffin OS v2 productivity system.

Today's date: {date.today().strftime('%A, %B %d, %Y')}

Your personality:
- Supportive and non-judgmental
- Concise (1-3 sentences per response, unless asked for details)
- Proactive (remind about logging, reviews, etc.)
- Practical (help break down goals into sessions)

Your role:
- Help users log daily work sessions (deep + shallow time)
- Track progress toward weekly goals
- Help capture and evaluate ideas
- Guide weekly reviews
- Send gentle reminders

{TOOLS_PROMPT}

Always be encouraging. If the user skipped logging, say "No worries, let's log it now!" not "You forgot again!"
"""

# ============================================================================
# TOOL EXECUTOR
# ============================================================================


def execute_tool(tool_call: str) -> str:
    """
    Parse and execute a tool call.
    Format: TOOL: TOOL_NAME(arg1, arg2, ...)
    """
    match = re.match(r"TOOL:\s*(\w+)\((.*)\)", tool_call.strip())
    if not match:
        return "❌ Invalid tool format"

    tool_name = match.group(1).upper()
    args_str = match.group(2)

    # Simple argument parser (handles quoted strings)
    args = []
    in_quotes = False
    current_arg = ""
    for char in args_str:
        if char == '"' and (not current_arg or current_arg[-1] != "\\"):
            in_quotes = not in_quotes
        elif char == "," and not in_quotes:
            args.append(current_arg.strip().strip('"'))
            current_arg = ""
            continue
        current_arg += char
    if current_arg.strip():
        args.append(current_arg.strip().strip('"'))

    # Execute
    if tool_name == "LOG_SESSION" and len(args) >= 3:
        return log_session(int(args[0]), int(args[1]), args[2])
    elif tool_name == "GET_WEEK_PROGRESS":
        return get_week_progress()
    elif tool_name == "ADD_IDEA" and len(args) >= 2:
        return add_idea(args[0], args[1])
    elif tool_name == "SCORE_IDEAS":
        return score_ideas()
    elif tool_name == "GENERATE_REVIEW":
        return generate_review()
    elif tool_name == "CHECK_REMINDERS":
        return check_reminders()
    elif tool_name == "STREAKS":
        return streaks()
    elif tool_name == "SET_STREAK_GOAL" and len(args) >= 1:
        try:
            from scripts import streaks as _streaks
            return _streaks.set_streak_goal(int(args[0]))
        except Exception as e:
            return f"❌ Error setting goal: {e}"
    elif tool_name == "STREAK_HEATMAP":
        try:
            from scripts import streaks as _streaks
            return _streaks.generate_heatmap()
        except Exception as e:
            return f"❌ Error generating heatmap: {e}"
    elif tool_name == "SEARCH_REVIEWS":
        # Expect single string arg
        if len(args) >= 1:
            try:
                from scripts import rag

                results = rag.search_reviews(args[0], top_k=5)
                if not results:
                    return (
                        "🔎 No weekly reviews found. Add files under "
                        "weekly_reviews/ and build the index with "
                        "scripts/rag.py --build"
                    )
                out_lines = []
                for path, chunk, score in results:
                    out_lines.append(
                        f"{score:.3f} - {Path(path).name}: "
                        f"{chunk[:300].strip()}"
                    )
                return "\n\n".join(out_lines)
            except Exception as e:
                return f"❌ RAG error: {e}"
        return "❌ SEARCH_REVIEWS requires a query string"
    else:
        return f"❌ Unknown tool: {tool_name}"

# ============================================================================
# MAIN CHAT LOOP
# ============================================================================


def chat_loop():
    """Main conversation loop."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Load history if exists
    history = load_chat_history()
    if history:
        messages = history
        print("\n📚 Loaded previous conversation.\n")

    # Check reminders on startup
    print("🔍 Checking for reminders...")
    reminders = check_reminders()
    if "📋" in reminders or "📝" in reminders:
        print(f"\n{reminders}\n")

    print(
        f"💭 Saffin Assistant ({CONFIG.model}) ready.\n"
        "Type 'clear', 'history', or 'exit' for commands.\n"
    )

    while True:
        try:
            user_input = input("You: ").strip()
        except KeyboardInterrupt:
            print("\n\nGoodbye! 👋")
            save_chat_history(messages)
            break

        if not user_input:
            continue

        # Commands
        if user_input.lower() == "exit":
            print("Goodbye! 👋")
            save_chat_history(messages)
            break
        elif user_input.lower() == "clear":
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            print("Conversation cleared.\n")
            continue
        elif user_input.lower() == "history":
            print("\n📜 Conversation history:")
            for i, msg in enumerate(messages):
                if msg["role"] != "system":
                    print(f"  {i}. {msg['role'].upper()}: {msg['content'][:60]}...")
            print()
            continue

        # Add user message
        messages.append({"role": "user", "content": user_input})

        # Get response (streamed if enabled)
        full_response = call_ollama(messages, stream=CONFIG.stream)

        # If streaming, the assistant text was printed live by call_ollama
        # Check for tool calls after streaming completes
        if "TOOL:" in full_response:
            lines = full_response.split("\n")
            tool_calls = [l.strip() for l in lines if l.strip().startswith("TOOL:")]

            # Execute and print tool results
            for tool_call in tool_calls:
                result = execute_tool(tool_call)
                print(f"  {result}")

        else:
            # If not streaming, print the assistant response
            if not CONFIG.stream:
                print(f"\nSaffin: {full_response}\n")

        # Add assistant message to history and save
        messages.append({"role": "assistant", "content": full_response})
        save_chat_history(messages)

# ============================================================================
# CLI COMMANDS (for non-interactive use)
# ============================================================================


def cli_mode(args: List[str]):
    """Non-interactive mode for scripting."""
    if not args:
        chat_loop()
        return

    command = args[0].lower()
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if command == "log":
        # saffin.py assistant log 30 20 "notes here"
        if len(args) < 4:
            print("Usage: assistant log <primary> <secondary> <notes>")
            return
        result = log_session(int(args[1]), int(args[2]), " ".join(args[3:]))
        print(result)

    elif command == "status":
        result = get_week_progress()
        print(result)

    elif command == "idea":
        if len(args) < 3:
            print("Usage: assistant idea <title> <description>")
            return
        result = add_idea(args[1], " ".join(args[2:]))
        print(result)

    elif command == "reminders":
        result = check_reminders()
        print(result)

    elif command == "streaks":
        print(streaks())
    elif command == "goal":
        # assistant goal [days]
        if len(args) < 2:
            try:
                from scripts import streaks as _streaks
                goal = _streaks.get_streak_goal()
                print(f"Current goal: {goal or 'not set'}")
            except Exception as e:
                print(f"Error: {e}")
        else:
            try:
                from scripts import streaks as _streaks
                print(_streaks.set_streak_goal(int(args[1])))
            except Exception as e:
                print(f"Error setting goal: {e}")
    elif command == "heatmap":
        try:
            from scripts import streaks as _streaks
            print(_streaks.generate_heatmap())
        except Exception as e:
            print(f"Error generating heatmap: {e}")
    elif command == "search_reviews":
        query = " ".join(args[1:]) if len(args) > 1 else None
        if not query:
            print("Usage: assistant.py search_reviews <query>")
            return
        try:
            from scripts import rag
            results = rag.search_reviews(query, top_k=5)
            if not results:
                print("No reviews found.")
                return
            for path, chunk, score in results:
                print(f"{score:.3f} - {Path(path).name}\n{chunk}\n---\n")
        except Exception as e:
            print(f"RAG error: {e}")

    elif command == "ask":
        # saffin.py assistant ask "Natural language query"
        query = " ".join(args[1:])
        messages.append({"role": "user", "content": query})
        response = call_ollama(messages, stream=CONFIG.stream)
        if not CONFIG.stream:
            print(response)

    else:
        print(f"Unknown command: {command}")
        print("Available: log, status, idea, reminders, ask, or leave blank for chat mode")

# ============================================================================
# ENTRY POINT
# ============================================================================


if __name__ == "__main__":
    # Parse global flags first
    parser = argparse.ArgumentParser(
        description="Saffin Assistant — local AI for Saffin OS v2",
        add_help=False,
    )
    parser.add_argument(
        "--model", default=CONFIG.model,
        help=f"Ollama model (default: {CONFIG.model})"
    )
    parser.add_argument(
        "--no-stream", action="store_true",
        help="Disable streaming output"
    )
    parser.add_argument(
        "--host", default=CONFIG.host,
        help=f"Ollama host (default: {CONFIG.host})"
    )
    parser.add_argument("-h", "--help", action="store_true")

    known, remaining = parser.parse_known_args()

    # Override CONFIG
    CONFIG.model = known.model
    CONFIG.host = known.host
    CONFIG.stream = not known.no_stream

    if known.help and not remaining:
        parser.print_help()
        print("\nCommands: log, status, idea, reminders, ask")
        print("Or run with no command for interactive chat.")
        sys.exit(0)

    if remaining:
        cli_mode(remaining)
    else:
        if CONFIG.stream:
            # check setup but continue if not available
            ok = check_setup()
            if not ok:
                print("Running in fallback mode without Ollama.")
        chat_loop()
