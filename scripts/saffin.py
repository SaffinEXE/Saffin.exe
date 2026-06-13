#!/usr/bin/env python3
"""
saffin.py — Automation CLI for Saffin OS v2

Commands:
  log       Append a journal entry
  idea      Add a new idea to the idea vault
  score     Score unscored ideas that are 48h+ old
  review    Generate this week's review file from journal data
  status    Show quick status (sessions this week, pending ideas)

Run `python saffin.py <command> --help` for details.
"""

import argparse
import csv
import os
import re
import sys
import subprocess
from datetime import datetime, timedelta

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)  # Saffin_OS_v2/
JOURNAL_CSV = os.path.join(ROOT, "journal", "journal.csv")
IDEA_VAULT = os.path.join(ROOT, "idea_vault.md")
WEEKLY_DIR = os.path.join(ROOT, "weekly_reviews")
WEEKLY_TEMPLATE = os.path.join(WEEKLY_DIR, "TEMPLATE.md")

sys.path.insert(0, BASE)
from decision_score import decision_score  # noqa: E402


# ---------------------------------------------------------------------------
# log: append a journal entry
# ---------------------------------------------------------------------------
def cmd_log(args):
    date = args.date or datetime.now().strftime("%Y-%m-%d")
    primary = args.primary
    secondary = args.secondary
    notes = args.notes or ""

    file_exists = os.path.isfile(JOURNAL_CSV)
    with open(JOURNAL_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["date", "primary_minutes", "secondary_minutes", "notes"])
        writer.writerow([date, primary, secondary, notes])

    print(f"Logged: {date} | Primary: {primary}m | Secondary: {secondary}m | Notes: {notes}")


# ---------------------------------------------------------------------------
# idea: append a new idea to idea_vault.md
# ---------------------------------------------------------------------------
def cmd_idea(args):
    date_added = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = f"""
### {args.title}
- Date added: {date_added}
- Description: {args.description or ""}
- Impact (1-5): 
- Alignment (1-5): 
- Effort (1-5): 
- Risk (1-5): 
- Opportunity Cost (1-5): 
- Score: 
- Action: [Vault / Act / Drop]
"""
    with open(IDEA_VAULT, "a", encoding="utf-8") as f:
        f.write(entry)

    print(f"Idea added: '{args.title}' (added {date_added})")
    print("It will be eligible for scoring after 48 hours (use `python saffin.py score`).")


# ---------------------------------------------------------------------------
# score: find unscored ideas 48h+ old and prompt scoring
# ---------------------------------------------------------------------------
IDEA_BLOCK_RE = re.compile(
    r"### (.+?)\n"
    r"- Date added: (.+?)\n"
    r"- Description: (.*?)\n"
    r"- Impact \(1-5\): (.*?)\n"
    r"- Alignment \(1-5\): (.*?)\n"
    r"- Effort \(1-5\): (.*?)\n"
    r"- Risk \(1-5\): (.*?)\n"
    r"- Opportunity Cost \(1-5\): (.*?)\n"
    r"- Score: (.*?)\n"
    r"- Action: (.*?)(?:\n|$)"
)


def cmd_score(args):
    if not os.path.isfile(IDEA_VAULT):
        print("idea_vault.md not found.")
        return

    with open(IDEA_VAULT, "r", encoding="utf-8") as f:
        content = f.read()

    now = datetime.now()
    matches = list(IDEA_BLOCK_RE.finditer(content))

    if not matches:
        print("No ideas found in idea_vault.md.")
        return

    eligible = []
    for m in matches:
        title, date_added_str, desc, impact, align, effort, risk, opp, score, action = m.groups()
        score = score.strip()
        action = action.strip()
        if score and action in ("Act", "Vault", "Drop"):
            continue  # already scored

        try:
            date_added = datetime.strptime(date_added_str.strip(), "%Y-%m-%d %H:%M")
        except ValueError:
            try:
                date_added = datetime.strptime(date_added_str.strip(), "%Y-%m-%d")
            except ValueError:
                continue

        if now - date_added >= timedelta(hours=48):
            eligible.append((m, title.strip(), date_added))

    if not eligible:
        print("No ideas are ready for scoring (either none are 48h+ old, or all are scored).")
        return

    print(f"Found {len(eligible)} idea(s) ready for scoring:\n")

    new_content = content
    for m, title, date_added in eligible:
        print(f"--- {title} (added {date_added.strftime('%Y-%m-%d %H:%M')}) ---")
        try:
            impact = int(input("  Impact (1-5): "))
            alignment = int(input("  Alignment (1-5): "))
            effort = int(input("  Effort (1-5): "))
            risk = int(input("  Risk (1-5): "))
            opp_cost = int(input("  Opportunity Cost (1-5): "))
        except (ValueError, EOFError, KeyboardInterrupt):
            print("  Skipped (invalid input or interrupted).\n")
            continue

        score, interpretation = decision_score(impact, alignment, effort, risk, opp_cost)
        action_word = {
            "Act now": "Act",
            "Vault (revisit next quarter)": "Vault",
            "Drop": "Drop",
        }.get(interpretation, "Vault")

        print(f"  => Score: {score} | {interpretation}\n")

        # Replace this block's fields in new_content
        old_block = m.group(0)
        new_block = old_block
        new_block = re.sub(r"- Impact \(1-5\): .*", f"- Impact (1-5): {impact}", new_block)
        new_block = re.sub(r"- Alignment \(1-5\): .*", f"- Alignment (1-5): {alignment}", new_block)
        new_block = re.sub(r"- Effort \(1-5\): .*", f"- Effort (1-5): {effort}", new_block)
        new_block = re.sub(r"- Risk \(1-5\): .*", f"- Risk (1-5): {risk}", new_block)
        new_block = re.sub(r"- Opportunity Cost \(1-5\): .*", f"- Opportunity Cost (1-5): {opp_cost}", new_block)
        new_block = re.sub(r"- Score: .*", f"- Score: {score}", new_block)
        new_block = re.sub(r"- Action: .*", f"- Action: {action_word}", new_block)

        new_content = new_content.replace(old_block, new_block)

    with open(IDEA_VAULT, "w", encoding="utf-8") as f:
        f.write(new_content)

    print("idea_vault.md updated.")


# ---------------------------------------------------------------------------
# review: generate this week's review file pre-filled from journal data
# ---------------------------------------------------------------------------
def cmd_review(args):
    today = datetime.now()
    # Find the most recent Sunday (or today if Sunday)
    days_since_sunday = (today.weekday() + 1) % 7
    week_end = today - timedelta(days=days_since_sunday)
    week_start = week_end - timedelta(days=6)

    primary_sessions = 0
    secondary_sessions = 0
    primary_minutes_total = 0
    secondary_minutes_total = 0

    if os.path.isfile(JOURNAL_CSV):
        with open(JOURNAL_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    d = datetime.strptime(row["date"].strip(), "%Y-%m-%d")
                except (ValueError, KeyError):
                    continue
                if week_start.date() <= d.date() <= week_end.date():
                    pm = int(row.get("primary_minutes", 0) or 0)
                    sm = int(row.get("secondary_minutes", 0) or 0)
                    if pm > 0:
                        primary_sessions += 1
                        primary_minutes_total += pm
                    if sm > 0:
                        secondary_sessions += 1
                        secondary_minutes_total += sm

    exec_score_primary = round((primary_sessions / 5) * 100) if primary_sessions else 0
    exec_score_secondary = round((secondary_sessions / 3) * 100) if secondary_sessions else 0

    filename = os.path.join(WEEKLY_DIR, f"{week_end.strftime('%Y-%m-%d')}.md")

    if os.path.isfile(filename) and not args.force:
        print(f"{filename} already exists. Use --force to overwrite.")
        return

    content = f"""# Weekly Review

- **Date:** {week_end.strftime('%Y-%m-%d')} (week of {week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')})
- **Primary sessions:** {primary_sessions} / 5  ({primary_minutes_total} min total)
- **Secondary sessions:** {secondary_sessions} / 3  ({secondary_minutes_total} min total)
- **Protein days:** __ / 7
- **Execution Score (Primary):** {exec_score_primary}%
- **Execution Score (Secondary):** {exec_score_secondary}%

## Reflection
- **One thing finished:**
- **One thing avoided:**
- **Smallest next action for Primary:**

## Idea Vault Check
Run `python saffin.py score` to process any items 48h+ old.
"""

    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Weekly review created: {filename}")
    print(f"Primary sessions: {primary_sessions}/5 | Secondary sessions: {secondary_sessions}/3")


# ---------------------------------------------------------------------------
# status: quick overview
# ---------------------------------------------------------------------------
def cmd_status(args):
    today = datetime.now()
    days_since_sunday = (today.weekday() + 1) % 7
    week_start = today - timedelta(days=days_since_sunday)

    primary_sessions = 0
    secondary_sessions = 0

    if os.path.isfile(JOURNAL_CSV):
        with open(JOURNAL_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    d = datetime.strptime(row["date"].strip(), "%Y-%m-%d")
                except (ValueError, KeyError):
                    continue
                if week_start.date() <= d.date() <= today.date():
                    pm = int(row.get("primary_minutes", 0) or 0)
                    sm = int(row.get("secondary_minutes", 0) or 0)
                    if pm > 0:
                        primary_sessions += 1
                    if sm > 0:
                        secondary_sessions += 1

    print(f"Status as of {today.strftime('%Y-%m-%d')} (week starting {week_start.strftime('%Y-%m-%d')}):")
    print(f"  Primary sessions this week:   {primary_sessions} / 5")
    print(f"  Secondary sessions this week: {secondary_sessions} / 3")

    # Pending ideas (unscored)
    pending = 0
    ready = 0
    if os.path.isfile(IDEA_VAULT):
        with open(IDEA_VAULT, "r", encoding="utf-8") as f:
            content = f.read()
        for m in IDEA_BLOCK_RE.finditer(content):
            title, date_added_str, desc, impact, align, effort, risk, opp, score, action = m.groups()
            score = score.strip()
            action = action.strip()
            if score and action in ("Act", "Vault", "Drop"):
                continue
            pending += 1
            try:
                date_added = datetime.strptime(date_added_str.strip(), "%Y-%m-%d %H:%M")
            except ValueError:
                try:
                    date_added = datetime.strptime(date_added_str.strip(), "%Y-%m-%d")
                except ValueError:
                    continue
            if today - date_added >= timedelta(hours=48):
                ready += 1

    print(f"  Unscored ideas: {pending} ({ready} ready for scoring — run `python saffin.py score`)")

    if today.weekday() == 6:  # Sunday
        print("\n  🔔 It's Sunday — time for your weekly review! Run `python saffin.py review`")


# ---------------------------------------------------------------------------
# chat: start the interactive assistant
# ---------------------------------------------------------------------------
def cmd_chat(args):
    assistant_path = os.path.join(BASE, "assistant.py")
    if not os.path.isfile(assistant_path):
        print("assistant.py not found in scripts/. Make sure assistant.py exists.")
        return
    subprocess.run([sys.executable, assistant_path])


# ---------------------------------------------------------------------------
# CLI setup
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Saffin OS v2 automation CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_log = sub.add_parser("log", help="Append a journal entry")
    p_log.add_argument("primary", type=int, help="Primary minutes")
    p_log.add_argument("secondary", type=int, help="Secondary minutes")
    p_log.add_argument("--notes", type=str, default="", help="Notes for the day")
    p_log.add_argument("--date", type=str, default=None, help="Date (YYYY-MM-DD), defaults to today")
    p_log.set_defaults(func=cmd_log)

    p_idea = sub.add_parser("idea", help="Add a new idea to the idea vault")
    p_idea.add_argument("title", type=str, help="Idea title")
    p_idea.add_argument("--description", type=str, default="", help="Short description")
    p_idea.set_defaults(func=cmd_idea)

    p_score = sub.add_parser("score", help="Score unscored ideas that are 48h+ old")
    p_score.set_defaults(func=cmd_score)

    p_review = sub.add_parser("review", help="Generate this week's review file from journal data")
    p_review.add_argument("--force", action="store_true", help="Overwrite existing review file")
    p_review.set_defaults(func=cmd_review)

    p_status = sub.add_parser("status", help="Show quick status")
    p_status.set_defaults(func=cmd_status)

    p_chat = sub.add_parser("chat", help="Start the AI assistant (interactive)")
    p_chat.set_defaults(func=cmd_chat)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
