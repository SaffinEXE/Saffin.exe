from types import SimpleNamespace
import csv
import os
from datetime import datetime
from pathlib import Path

import scripts.saffin as saffin


def test_cmd_log(tmp_path):
    saffin.JOURNAL_CSV = str(tmp_path / "journal.csv")
    args = SimpleNamespace(primary=30, secondary=20, notes="note", date=None)
    saffin.cmd_log(args)
    text = Path(saffin.JOURNAL_CSV).read_text(encoding="utf-8")
    assert "30" in text


def test_cmd_idea(tmp_path):
    saffin.IDEA_VAULT = str(tmp_path / "idea_vault.md")
    args = SimpleNamespace(title="Test Idea", description="Desc")
    saffin.cmd_idea(args)
    content = Path(saffin.IDEA_VAULT).read_text(encoding="utf-8")
    assert "### Test Idea" in content


def test_cmd_review(tmp_path):
    saffin.JOURNAL_CSV = str(tmp_path / "journal.csv")
    saffin.WEEKLY_DIR = str(tmp_path / "weekly_reviews")
    os.makedirs(saffin.WEEKLY_DIR, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    with open(saffin.JOURNAL_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "primary_minutes", "secondary_minutes", "notes"])
        writer.writerow([today, "30", "20", "notes"])
    saffin.cmd_review(SimpleNamespace(force=True))
    md_files = list(Path(saffin.WEEKLY_DIR).glob("*.md"))
    assert len(md_files) == 1
