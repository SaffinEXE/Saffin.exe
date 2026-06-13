#!/usr/bin/env python3
"""
Decision Framework Calculator — Saffin OS v2

Score = Impact + Alignment + Opportunity Cost - Effort - Risk
Each input rated 1-5.

>= 15 -> Act
5-14  -> Vault
< 5   -> Drop

Usage:
  Interactive: python decision_score.py
  CLI args:    python decision_score.py <impact> <alignment> <effort> <risk> <opportunity_cost>
"""

import sys


def interpret(score):
    if score >= 15:
        return "Act"
    elif score >= 5:
        return "Vault"
    else:
        return "Drop"


def compute(impact, alignment, effort, risk, opportunity_cost):
    return impact + alignment + opportunity_cost - effort - risk


def decision_score(impact, alignment, effort, risk, opportunity_cost):
    """Returns (score, interpretation) — used by saffin.py automation CLI."""
    score = compute(impact, alignment, effort, risk, opportunity_cost)
    label = interpret(score)
    mapping = {"Act": "Act now", "Vault": "Vault (revisit next quarter)", "Drop": "Drop"}
    return score, mapping[label]


def get_int(prompt):
    while True:
        try:
            val = int(input(prompt))
            if 1 <= val <= 5:
                return val
            print("Please enter a number between 1 and 5.")
        except ValueError:
            print("Please enter a valid integer.")


def main():
    if len(sys.argv) == 6:
        try:
            impact, alignment, effort, risk, opp_cost = [int(x) for x in sys.argv[1:6]]
        except ValueError:
            print("All arguments must be integers 1-5.")
            sys.exit(1)
    elif len(sys.argv) == 1:
        print("Decision Framework — rate each factor 1 (low) to 5 (high)\n")
        impact = get_int("Impact (1-5): ")
        alignment = get_int("Alignment (1-5): ")
        effort = get_int("Effort (1-5): ")
        risk = get_int("Risk (1-5): ")
        opp_cost = get_int("Opportunity Cost (1-5): ")
    else:
        print("Usage:")
        print("  python decision_score.py")
        print("  python decision_score.py <impact> <alignment> <effort> <risk> <opportunity_cost>")
        sys.exit(1)

    score = compute(impact, alignment, effort, risk, opp_cost)
    decision = interpret(score)

    print(f"\nScore: {score}")
    print(f"Decision: {decision}")


if __name__ == "__main__":
    main()
