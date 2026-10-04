# Prompt Learning Platform

A Streamlit app that teaches students to write better AI prompts, with a prompt library, graded learning modules and three tiers: Free, Plus and Pro.

**Copyright (c) 2026 Kyrvyn Ltd (kyrvynltd.co.uk), company number 17246800. All rights reserved.** See [LICENSE](LICENSE) and [docs/OWNERSHIP.md](docs/OWNERSHIP.md).

## What it does

| Area | Description | Free | Plus | Pro |
|---|---|---|---|---|
| **Prompt analyser** (home) | Scores a prompt against best-practice checks and suggests an improved version | yes | yes | yes |
| **Practice mode** | 10 graded exercises over 3 levels, instant rubric feedback | yes | yes | yes |
| **Library** | 130 prompts in 13 categories with search and filters | free prompts | all prompts | all prompts |
| **Student Success pack** | 15 study prompts built to teach, not ghost-write | 6 | 15 | 15 |
| **Learn** | 5 modules, 15 graded exercises, saved progress | module 1 | modules 1-4 | all 5 (advanced track) |
| **Workspace and templates** | Personal prompt workspace with export, 8 templates | no | no | yes |
| **AI feedback** | Capped monthly AI review of a prompt. Off until an API key is set | no | no | yes |
| **Accounts** | Email sign-in, student verification (.ac.uk), data export and deletion | yes | yes | yes |

Prices (configurable): Plus 4.99 GBP/month or 39.99 GBP/year, Pro 9.99 GBP/month or 99.99 GBP/year. See [docs/PAYMENTS.md](docs/PAYMENTS.md). Workshop access codes grant Pro.

Prompt analysis and Practice grading are heuristic and run locally (no AI calls, no data leaves the app). They check the structure of a prompt, not whether an AI's answer is true.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate   # Python 3.10+
pip install -r requirements-dev.txt
cp .env.example .env                                  # optional: configuration
streamlit run src/app.py
```

Open http://localhost:8501. With no `DATABASE_URL` the app uses a local SQLite file.

## Quality checks

```bash
ruff check .
mypy
pytest --cov        # fails below 95% coverage
```

CI runs these on Python 3.10 and 3.12, plus a secret scan and a dependency audit (`.github/workflows/ci.yml`).

## Payments status

Checkout and webhook code for Stripe, Lemon Squeezy and PayPal is in the repository and tested against mocked provider events. It has not been connected to any live provider account, and nothing charges anyone until the owner creates the products, sets the checkout links and webhook secrets, and deploys the webhook service. See [docs/PAYMENTS.md](docs/PAYMENTS.md).

Access codes (workshops, vouchers) work without a payment provider:

```bash
export ENTITLEMENT_SECRET="$(python -c 'import secrets;print(secrets.token_urlsafe(32))')"
python scripts/issue_access_code.py student@example.ac.uk pro 30
```

With no `ENTITLEMENT_SECRET` set, codes are disabled (fail closed). Premium prompt text lives in this repository, so keep the repository private.

## Project layout

```
src/app.py              Home: prompt analyser (UI)
src/pages/              Practice, Library, Account, Learn, Workspace, AI feedback pages
src/analysis.py         Prompt analysis logic (no UI)
src/db.py               SQLite / Postgres layer and migrations
src/accounts.py         Accounts, sessions, password reset, student verification
src/billing.py          Stripe / Lemon Squeezy / PayPal adapters, entitlements, checkout links
src/webhook_server.py   Payment webhook receiver
src/learning.py         Modules, grading, progress
src/workspace.py        Pro prompt workspace
src/ai_feedback.py      Pro AI feedback (capped, off by default)
src/audit.py            Security audit log
src/retention.py        Data retention purge
src/brand.py            Owner details shown across the product
src/entitlements.py     Signed access codes
src/tiers.py, pricing.py  Plan tiers and prices
data/modules/           Learning modules (JSON)
data/templates.json     Template pack
prompts/                Prompt library (JSON, one file per prompt)
scripts/                Access codes, purge, backup, build tools
docs/                   Guides, policies and compliance (start at docs/README.md)
tests/                  pytest suite
```

## Deployment

`render.yaml` and the `Dockerfile` are configured conservatively: free plan and manual deploys, so merging code never deploys or charges by itself. See [docs/DEPLOYMENT_RUNBOOK.md](docs/DEPLOYMENT_RUNBOOK.md). Set secrets in the host dashboard, never in git.

## Responsible use

See [docs/ACADEMIC_INTEGRITY.md](docs/ACADEMIC_INTEGRITY.md). Students must follow their institution's AI policy. Prompts about legal, health or financial topics give general information, not professional advice.

## Prompt schema

See [docs/SCHEMA_V2_SPECIFICATION.md](docs/SCHEMA_V2_SPECIFICATION.md). Student Success prompts add `access` (`free` or `premium`), `audience`, `example_input` and `integrity_note`.

## Security, privacy and legal

Aligned with UK GDPR and ISO 27001-style controls. Not certified. Start at [docs/README.md](docs/README.md) for the full list: [SECURITY.md](SECURITY.md), [docs/PRIVACY.md](docs/PRIVACY.md), [docs/TERMS.md](docs/TERMS.md), [docs/COMPLIANCE_GAP_REVIEW.md](docs/COMPLIANCE_GAP_REVIEW.md), [docs/OWNERSHIP.md](docs/OWNERSHIP.md). Legal texts are drafts until a solicitor has reviewed them.
