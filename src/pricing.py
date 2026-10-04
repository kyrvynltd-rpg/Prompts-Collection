"""Plan prices. Display only: the real amount is whatever you set in the payment provider.

Defaults: Plus 4.99/month or 39.99/year, Pro 9.99/month or 99.99/year. Override with environment variables, e.g.
PRICE_PLUS_MONTHLY_GBP=5.99. No code change needed.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

DEFAULTS = {("plus", "monthly"): "4.99", ("plus", "annual"): "39.99", ("pro", "monthly"): "9.99", ("pro", "annual"): "99.99"}


@dataclass(frozen=True)
class Price:
    amount: float
    period: str  # "monthly" or "annual"
    symbol: str = "\u00a3"

    def label(self) -> str:
        return f"{self.symbol}{self.amount:.2f}/{'month' if self.period == 'monthly' else 'year'}"


@dataclass(frozen=True)
class Pricing:
    prices: dict[tuple[str, str], Price]

    def get(self, tier: str, period: str) -> Price:
        return self.prices[(tier, period)]

    def annual_saving_percent(self, tier: str) -> int:
        monthly, annual = self.get(tier, "monthly").amount, self.get(tier, "annual").amount
        return max(0, round((1 - annual / (monthly * 12)) * 100))


def _price(tier: str, period: str) -> float:
    default = DEFAULTS[(tier, period)]
    try:
        value = float(os.getenv(f"PRICE_{tier.upper()}_{period.upper()}_GBP", default))
    except ValueError:
        value = float(default)
    return value if value > 0 else float(default)


def get_pricing() -> Pricing:
    return Pricing({k: Price(_price(*k), k[1]) for k in DEFAULTS})
