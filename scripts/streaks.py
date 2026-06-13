"""
Streak tracking: goals, progress, and heatmap visualization.
Works standalone (no Ollama required).
"""
import json
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

# Config file for streak goal
CONFIG_FILE = Path(__file__).resolve().parent.parent / ".saffin_config.json"
JOURNAL_CSV = Path(__file__).resolve().parent.parent / "journal" / "journal.csv"


def load_config() -> dict:
    """Load config from .saffin_config.json."""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_config(config: dict):
    """Save config to .saffin_config.json."""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def get_streak_goal() -> Optional[int]:
    """Get the current streak goal (days), or None if not set."""
    return load_config().get("streak_goal")


def set_streak_goal(days: int) -> str:
    """Set the streak goal. Returns confirmation message."""
    if days < 1:
        return "❌ Goal must be at least 1 day."
    config = load_config()
    config["streak_goal"] = days
    save_config(config)
    return f"✅ Streak goal set to {days} days."


def calculate_streaks() -> dict:
    """Calculate current and longest streaks from journal.csv."""
    if not JOURNAL_CSV.exists():
        return {"current_streak": 0, "longest_streak": 0, "total_days": 0, "last_logged": None, "is_on_streak": False}

    dates = set()
    with open(JOURNAL_CSV, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line or (i == 0 and line.lower().startswith("date")):
                continue
            try:
                dates.add(date.fromisoformat(line.split(",")[0].strip()))
            except ValueError:
                continue

    if not dates:
        return {"current_streak": 0, "longest_streak": 0, "total_days": 0, "last_logged": None, "is_on_streak": False}

    sorted_dates = sorted(dates)
    today = date.today()
    last_logged = sorted_dates[-1]
    is_on_streak_today = last_logged == today

    # Current streak
    current_streak = 0
    cursor = last_logged
    while cursor in dates:
        current_streak += 1
        cursor -= timedelta(days=1)
    if (today - last_logged).days > 1:
        current_streak = 0

    # Longest streak
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
        "last_logged": last_logged.isoformat(),
        "is_on_streak": is_on_streak_today,
    }


def progress_toward_goal() -> str:
    """Show progress bar toward streak goal."""
    goal = get_streak_goal()
    if not goal:
        return "🎯 No streak goal set. Use: `assistant goal <days>`"

    stats = calculate_streaks()
    current = stats["current_streak"]
    pct = min(100, int((current / goal) * 100))
    bar_len = 20
    filled = int(bar_len * current / goal)
    bar = "█" * filled + "░" * (bar_len - filled)

    if current >= goal:
        return f"🎯 Goal: {goal} days | ✅ **ACHIEVED!** ({current}/{goal})\n   {bar} {pct}%"
    else:
        remaining = goal - current
        return f"🎯 Goal: {goal} days | Current: {current} | Remaining: {remaining}\n   {bar} {pct}%"


def generate_heatmap(weeks: int = 12) -> str:
    """
    Generate ASCII heatmap of logged days (like GitHub contributions).
    Shows last `weeks` weeks (default 12 = ~3 months).
    """
    if not JOURNAL_CSV.exists():
        return "📊 No journal data yet. Start logging to see your heatmap!"

    dates = set()
    with open(JOURNAL_CSV, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line or (i == 0 and line.lower().startswith("date")):
                continue
            try:
                dates.add(date.fromisoformat(line.split(",")[0].strip()))
            except ValueError:
                continue

    if not dates:
        return "📊 No logged days yet."

    # Build grid: weeks x 7 days
    today = date.today()
    start_date = today - timedelta(weeks=weeks)
    # Align to Sunday
    start_date -= timedelta(days=start_date.weekday() + 1)

    grid = []
    for week in range(weeks + 1):
        col = []
        for day in range(7):
            d = start_date + timedelta(weeks=week, days=day)
            if d > today:
                col.append(" ")
            elif d in dates:
                col.append("█")
            else:
                col.append("░")
        grid.append(col)

    # Render as text
    lines = ["📊 Streak Heatmap (last {} weeks)".format(weeks), ""]
    day_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    for i, label in enumerate(day_labels):
        row = label + " "
        for week in range(len(grid)):
            row += grid[week][i] + " "
        lines.append(row)

    lines.append("")
    lines.append("Legend: █ = logged | ░ = not logged |   = future")
    return "\n".join(lines)


def streaks_summary() -> str:
    """Full streak summary with goal progress."""
    stats = calculate_streaks()
    goal = get_streak_goal()

    parts = []
    parts.append(f"🔥 Current streak: **{stats['current_streak']} day(s)**")
    parts.append(f"🏆 Longest streak: **{stats['longest_streak']} day(s)**")
    parts.append(f"📅 Total days logged: {stats['total_days']}")
    parts.append(f"📝 Last logged: {stats['last_logged'] or 'never'}")

    if stats["is_on_streak"]:
        parts.append("✅ You're logged in today — keep the streak alive!")
    else:
        parts.append("💡 Tip: log today to start a new streak.")

    if goal:
        parts.append("")
        parts.append(progress_toward_goal())

    return "\n".join(parts)
