"""Tests for streak goals and heatmap."""
import tempfile
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import streaks


def test_set_and_get_goal():
    """Setting a goal persists and retrieves correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = Path(tmpdir) / ".saffin_config.json"
        with patch.object(streaks, "CONFIG_FILE", config_file):
            result = streaks.set_streak_goal(30)
            assert "✅" in result
            assert streaks.get_streak_goal() == 30


def test_goal_not_set():
    """No goal returns None."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = Path(tmpdir) / ".saffin_config.json"
        with patch.object(streaks, "CONFIG_FILE", config_file):
            assert streaks.get_streak_goal() is None


def test_progress_no_goal():
    """Progress shows message when no goal is set."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = Path(tmpdir) / ".saffin_config.json"
        with patch.object(streaks, "CONFIG_FILE", config_file):
            result = streaks.progress_toward_goal()
            assert "No streak goal set" in result


def test_progress_with_goal():
    """Progress shows bar when goal is set."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = Path(tmpdir) / ".saffin_config.json"
        journal_file = Path(tmpdir) / "journal.csv"
        # Write 3 days of data
        today = date.today()
        with open(journal_file, "w") as f:
            f.write("date,primary_minutes,secondary_minutes,notes\n")
            for i in range(3):
                d = today - timedelta(days=i)
                f.write(f"{d.isoformat()},30,0,test\n")

        with patch.object(streaks, "CONFIG_FILE", config_file), \
             patch.object(streaks, "JOURNAL_CSV", journal_file):
            streaks.set_streak_goal(10)
            result = streaks.progress_toward_goal()
            assert "🎯" in result
            assert "30%" in result or "3/10" in result


def test_heatmap_no_data():
    """Heatmap shows message when no journal exists."""
    with tempfile.TemporaryDirectory() as tmpdir:
        journal_file = Path(tmpdir) / "journal.csv"
        with patch.object(streaks, "JOURNAL_CSV", journal_file):
            result = streaks.generate_heatmap()
            assert "No journal data" in result or "No logged days" in result


def test_heatmap_with_data():
    """Heatmap renders with logged days."""
    with tempfile.TemporaryDirectory() as tmpdir:
        journal_file = Path(tmpdir) / "journal.csv"
        today = date.today()
        with open(journal_file, "w") as f:
            f.write("date,primary_minutes,secondary_minutes,notes\n")
            for i in range(5):
                d = today - timedelta(days=i)
                f.write(f"{d.isoformat()},30,0,test\n")

        with patch.object(streaks, "JOURNAL_CSV", journal_file):
            result = streaks.generate_heatmap()
            assert "📊" in result
            assert "█" in result  # At least one logged day
            assert "Legend" in result
