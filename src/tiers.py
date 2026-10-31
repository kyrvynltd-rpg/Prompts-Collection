"""Plan tiers. Free < Plus < Pro. Old plan names map onto these so earlier access codes and grants keep working."""
from __future__ import annotations

import os

TIERS = ("free", "plus", "pro")
PLAN_TIER = {"student": "plus", "plus": "plus", "workshop": "pro", "pro": "pro"}
FEATURE_TIERS = {"workspace": "pro", "templates": "pro", "ai_feedback": "pro"}

PRO_FEATURES = ("AI prompt feedback (monthly cap)", "Personal prompt workspace with export",
                "Advanced course tracks", "Templates and workshop pack")


def rank(tier: str) -> int:
    return TIERS.index(tier) if tier in TIERS else 0


def tier_of_plan(plan: str | None) -> str:
    return PLAN_TIER.get(plan or "", "free")


def feature_tier(feature: str) -> str:
    override = os.getenv(f"TIER_{feature.upper()}", "").strip().lower()
    if override in TIERS:
        return override
    return FEATURE_TIERS.get(feature, "pro")


def allows(have: str, need: str) -> bool:
    return rank(have) >= rank(need)
