"""Owner details shown across the product. One place to change after the transfer to Kyrvyn Ltd.

Defaults are Kyrvyn Ltd's details as supplied by the owner (verify against Companies House before launch). Override with env vars if you
prefer not to edit code: OWNER_NAME, COMPANY_NUMBER, REGISTERED_OFFICE, SITE_URL, CONTACT_EMAIL.
"""
from __future__ import annotations

import os

YEAR = 2026


def _env(name: str, default: str) -> str:
    return os.getenv(name) or default


def owner_name() -> str:
    return _env("OWNER_NAME", "Kyrvyn Ltd")


def site_url() -> str:
    return _env("SITE_URL", "https://kyrvynltd.co.uk")


def company_line() -> str:
    return (f"{owner_name()}, registered in England and Wales, company number "
            f"{_env('COMPANY_NUMBER', '17246800')}, registered office {_env('REGISTERED_OFFICE', 'Office 15 Exning Road, E16 4NB')}.")


def contact_email() -> str:
    return _env("CONTACT_EMAIL", "info@kyrvynltd.co.uk")


def copyright_line() -> str:
    return f"Copyright \u00a9 {YEAR} {owner_name()}. All rights reserved."
