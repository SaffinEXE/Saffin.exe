import os
from datetime import datetime, timedelta
from pathlib import Path

import scripts.saffin as saffin


def test_cmd_score_interactive(tmp_path, monkeypatch):
    # Prepare idea_vault with one unscored idea older than 48h
    saffin.IDEA_VAULT = str(tmp_path / "idea_vault.md")
    old_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d %H:%M")
    content = f"""### Test Idea\n- Date added: {old_date}\n- Description: desc\n- Impact (1-5): \n- Alignment (1-5): \n- Effort (1-5): \n- Risk (1-5): \n- Opportunity Cost (1-5): \n- Score: \n- Action: [Vault / Act / Drop]\n"""
    Path(saffin.IDEA_VAULT).write_text(content, encoding="utf-8")

    # Provide inputs for Impact, Alignment, Effort, Risk, Opportunity Cost
    responses = iter(["5", "5", "1", "1", "5"])  # should produce a high score => Vault or Act
    monkeypatch.setattr("builtins.input", lambda prompt="": next(responses))

    saffin.cmd_score(None)

    result = Path(saffin.IDEA_VAULT).read_text(encoding="utf-8")
    assert "- Score:" in result
    assert "- Action:" in result
