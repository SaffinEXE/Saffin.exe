"""Smoke tests for the Saffin assistant (no Ollama required)."""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import assistant
import csv
import tempfile
from datetime import date, timedelta
from pathlib import Path


def test_check_reminders_runs():
    """check_reminders should never crash."""
    result = assistant.check_reminders()
    assert isinstance(result, str)
    assert len(result) > 0


def test_execute_tool_invalid_format():
    """Invalid tool calls should return a friendly error."""
    result = assistant.execute_tool("NOT A TOOL CALL")
    assert "❌" in result or "Invalid" in result


def test_execute_tool_unknown():
    """Unknown tool names should be caught."""
    result = assistant.execute_tool("TOOL: NONEXISTENT()")
    assert "Unknown" in result or "❌" in result


def test_log_session_calls_subprocess():
    """log_session should invoke saffin.py log."""
    with patch("assistant.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        result = assistant.log_session(30, 15, "test notes")
        assert "✅" in result
        mock_run.assert_called_once()


def test_call_ollama_handles_connection_error():
    """If Ollama is down, return a friendly error not a crash."""
    with patch("assistant.requests.post") as mock_post:
        mock_post.side_effect = Exception("Connection refused")
        result = assistant.call_ollama([{"role": "user", "content": "hi"}])
        assert "❌" in result or "Error" in result


def test_call_ollama_handles_stream_disabled():
    """Non-streaming mode should still work."""
    with patch("assistant.requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {"content": "hello"}}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = assistant.call_ollama(
            [{"role": "user", "content": "hi"}],
            stream=False
        )
        assert result == "hello"


def test_check_setup_handles_missing_ollama():
    """check_setup should return False when Ollama is unreachable."""
    with patch("assistant.requests.get") as mock_get:
        mock_get.side_effect = Exception("Connection refused")
        result = assistant.check_setup()
        assert result is False


def _write_journal(rows):
    """Helper: write a temporary journal.csv with given (date, p, s, notes) rows."""
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False, encoding="utf-8", newline=""
    )
    writer = csv.writer(tmp)
    writer.writerow(["date", "primary_minutes", "secondary_minutes", "notes"])
    for r in rows:
        writer.writerow(r)
    tmp.close()
    return Path(tmp.name)


def test_streaks_no_file():
    """No journal file → empty streak state."""
    with patch.object(assistant, "JOURNAL_CSV", Path("/nonexistent/journal.csv")):
        result = assistant.calculate_streaks()
        assert result["current_streak"] == 0
        assert result["longest_streak"] == 0
        assert result["total_days"] == 0
        assert result["last_logged"] is None
        assert result["is_on_streak"] is False


def test_streaks_empty_journal():
    """Journal with only header → empty streak state."""
    tmp = _write_journal([])
    with patch.object(assistant, "JOURNAL_CSV", tmp):
        result = assistant.calculate_streaks()
        assert result["current_streak"] == 0
        assert result["total_days"] == 0


def test_streaks_current_streak_today():
    """Logged today and yesterday → 2-day current streak."""
    today = date.today()
    yesterday = today - timedelta(days=1)
    tmp = _write_journal([
        [yesterday.isoformat(), 30, 10, "day 1"],
        [today.isoformat(), 25, 5, "day 2"],
    ])
    with patch.object(assistant, "JOURNAL_CSV", tmp):
        result = assistant.calculate_streaks()
        assert result["current_streak"] == 2
        assert result["longest_streak"] == 2
        assert result["total_days"] == 2
        assert result["is_on_streak"] is True


def test_streaks_broken_streak():
    """Last log was 3 days ago → current streak is 0, longest is preserved."""
    today = date.today()
    old = today - timedelta(days=10)
    older = today - timedelta(days=11)
    tmp = _write_journal([
        [older.isoformat(), 30, 10, ""],
        [old.isoformat(), 30, 10, ""],
    ])
    with patch.object(assistant, "JOURNAL_CSV", tmp):
        result = assistant.calculate_streaks()
        assert result["current_streak"] == 0
        assert result["longest_streak"] == 2
        assert result["is_on_streak"] is False


def test_streaks_longest_preserved():
    """A 5-day streak from last month is still the longest even if current is 2."""
    today = date.today()
    rows = [
        [(today - timedelta(days=i)).isoformat(), 30, 0, ""] for i in range(2)
    ]
    # Add a 5-day streak from 30 days ago
    for i in range(5):
        rows.append([(today - timedelta(days=30 + i)).isoformat(), 30, 0, ""])
    tmp = _write_journal(rows)
    with patch.object(assistant, "JOURNAL_CSV", tmp):
        result = assistant.calculate_streaks()
        assert result["current_streak"] == 2
        assert result["longest_streak"] == 5


def test_streaks_returns_string():
    """The LLM-callable streaks() should return a formatted string."""
    with patch.object(assistant, "calculate_streaks") as mock_calc:
        mock_calc.return_value = {
            "current_streak": 3,
            "longest_streak": 7,
            "total_days": 10,
            "last_logged": date.today().isoformat(),
            "is_on_streak": True,
        }
        out = assistant.streaks()
        assert "🔥" in out
        assert "🏆" in out
        assert "3" in out
        assert "7" in out
        assert isinstance(out, str)
