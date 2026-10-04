"""Plan tiers. Free < Plus < Pro. Old plan names map onto these so earlier access codes and grants keep working."""
from __future__ import annotations

TIERS = ("free", "plus", "pro")
PLAN_TIER = {"student": "plus", "plus": "plus", "workshop": "pro", "pro": "pro"}

PRO_FEATURES = ("AI prompt feedback (monthly cap)", "Personal prompt workspace with export",
                "Advanced course tracks", "Templates and workshop pack")


def rank(tier: str) -> int:
    return TIERS.index(tier) if tier in TIERS else 0


def tier_of_plan(plan: str | None) -> str:
    return PLAN_TIER.get(plan or "", "free")


def allows(have: str, need: str) -> bool:
    return rank(have) >= rank(need)
