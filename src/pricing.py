"""Plan prices. Display only: the real amount is whatever you set in the payment provider.

Change them without touching code: PRICE_MONTHLY_GBP, PRICE_ANNUAL_GBP (e.g. PRICE_MONTHLY_GBP=9.99).
"""
from __future__ import annotations

import os
from dataclasses import dataclass

DEFAULT_MONTHLY = "4.99"
DEFAULT_ANNUAL = "39.99"


@dataclass(frozen=True)
class Pricing:
    monthly: float
    annual: float
    currency: str = "GBP"
    symbol: str = "£"

    @property
    def annual_saving_percent(self) -> int:
        return max(0, round((1 - self.annual / (self.monthly * 12)) * 100))

    def monthly_label(self) -> str:
        return f"{self.symbol}{self.monthly:.2f}/month"

    def annual_label(self) -> str:
        return f"{self.symbol}{self.annual:.2f}/year"


def _price(name: str, default: str) -> float:
    try:
        value = float(os.getenv(name, default))
    except ValueError:
        value = float(default)
    return value if value > 0 else float(default)


def get_pricing() -> Pricing:
    return Pricing(monthly=_price("PRICE_MONTHLY_GBP", DEFAULT_MONTHLY), annual=_price("PRICE_ANNUAL_GBP", DEFAULT_ANNUAL))
