import re
from pathlib import Path

import pytest

import retention
from pricing import get_pricing

ROOT = Path(__file__).resolve().parent.parent
LEGAL = ["docs/PRIVACY.md", "docs/TERMS.md", "docs/ROPA.md", "docs/SUBPROCESSORS.md", "docs/INCIDENT_RESPONSE.md",
         "docs/BACKUP_RESTORE.md", "docs/COMPLIANCE_GAP_REVIEW.md", "SECURITY.md", "LICENSE", "docs/OWNERSHIP.md"]
BRACKET = re.compile(r"\[([^\]\n]+)\](?!\()")


def read(name):
    return (ROOT / name).read_text(encoding="utf-8")


def test_every_placeholder_is_registered_or_flagged_for_the_solicitor():
    registry = read("docs/PLACEHOLDERS.md")
    for name in LEGAL:
        for token in BRACKET.findall(read(name)):
            if token.startswith("SOLICITOR TO CONFIRM") or token in ("x", " "):
                continue
            assert f"[{token}]" in registry, f"{name}: [{token}] is not listed in docs/PLACEHOLDERS.md"


def test_company_details_are_identical_everywhere():
    for name in ("docs/PRIVACY.md", "docs/TERMS.md"):
        text = read(name)
        assert "17246800" in text and "15 Exning Road, London, E16 4NB, United Kingdom" in text and "info@kyrvynltd.co.uk" in text
    assert "Office 15" not in "".join(read(n) for n in LEGAL)


def test_terms_prices_match_the_code_defaults():
    terms, p = read("docs/TERMS.md"), get_pricing()
    for tier in ("plus", "pro"):
        for period in ("monthly", "annual"):
            assert f"£{p.get(tier, period).amount:.2f}" in terms
    assert "£" not in read("docs/PRIVACY.md")


def test_retention_periods_in_privacy_match_the_code():
    privacy = read("docs/PRIVACY.md")
    for env, default_days, phrase in (("RETAIN_AUDIT_DAYS", 365, "12 months"), ("RETAIN_LOGIN_ATTEMPT_DAYS", 30, "Sign-in attempts | 30 days"),
                                      ("RETAIN_EVENT_DAYS", 730, "24 months"), ("RETAIN_AI_USAGE_DAYS", 400, "13 months")):
        assert retention._days(env, default_days) == default_days
        assert phrase in privacy, phrase
    import accounts
    assert accounts.SESSION_SECONDS == 14 * 86400 and "14 days" in privacy
    assert accounts.RESET_SECONDS == 3600 and accounts.VERIFY_SECONDS == 86400
    assert accounts.TERMS_VERSION in privacy and accounts.TERMS_VERSION in read("docs/TERMS.md")


def test_no_document_claims_certification_or_compliance():
    banned = re.compile(r"\b(ISO[ /]*27001[- ]certified|certified to ISO|fully compliant|is compliant with|guarantee[sd]? compliance)\b", re.I)
    for name in LEGAL + ["README.md", "docs/README.md"]:
        assert not banned.search(read(name)), name
    assert "not certified" in read("SECURITY.md") or "not certified" in read("README.md")


def test_readme_and_docs_index_links_resolve():
    for page in ("README.md", "docs/README.md"):
        base = (ROOT / page).parent
        for target in re.findall(r"\]\(([^)#]+?)(?:#[^)]*)?\)", read(page)):
            if target.startswith(("http", "mailto:")):
                continue
            assert (base / target).exists(), f"{page} links to missing {target}"


def test_no_stale_claims_in_readme():
    readme = read("README.md").lower()
    assert "no payment is taken in this app" not in readme
    assert "gabriele" not in readme


@pytest.mark.parametrize("name", ["docs/PRIVACY.md", "docs/TERMS.md"])
def test_legal_drafts_say_draft(name):
    assert "DRAFT" in read(name) and "solicitor" in read(name)
