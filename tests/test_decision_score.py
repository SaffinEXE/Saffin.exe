import pytest

from scripts import decision_score as ds


def test_compute_examples():
    assert ds.compute(4, 4, 2, 2, 3) == 7
    assert ds.compute(5, 5, 1, 1, 5) == 13


def test_interpret_boundaries():
    assert ds.interpret(15) == "Act"
    assert ds.interpret(14) == "Vault"
    assert ds.interpret(5) == "Vault"
    assert ds.interpret(4) == "Drop"


def test_decision_score_mapping():
    score, label = ds.decision_score(5, 5, 1, 1, 5)
    assert score == 13
    assert label == "Vault (revisit next quarter)"
