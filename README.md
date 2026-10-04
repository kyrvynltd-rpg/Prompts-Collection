# Prompt Learning Platform

A Streamlit app that teaches students to write better AI prompts and gives them a library of study-focused prompts, with a free tier and a premium tier.

**Copyright (c) 2026 Gabriele Iacopo Langellotto. All rights reserved.** See [LICENSE](LICENSE).

## What it does

| Area | Description | Access |
|---|---|---|
| **Prompt analyser** (home) | Scores a prompt against best-practice checks and suggests an improved version | Free |
| **Practice mode** | 10 graded exercises over 3 levels, instant rubric feedback, downloadable progress | Free |
| **Library** | 130 prompts in 13 categories with search and filters | Free + premium |
| **Student Success pack** | 15 study prompts (essay planning, feedback, revision, referencing, debugging, CV) built so they teach rather than ghost-write | 6 free, 9 premium |
| **Premium access** | Signed access codes unlock premium prompts. No payment is taken in this app | Needs code |

Scoring is heuristic and offline (no AI calls, no data leaves the app). It checks the structure of a prompt, not whether an AI's answer is true.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate   # Python 3.10+
pip install -r requirements-dev.txt
streamlit run src/app.py
```

Open http://localhost:8501.

## Tests

```bash
ruff check src tests scripts
pytest -q
```

CI runs both on Python 3.10 and 3.12 (`.github/workflows/ci.yml`).

## Premium access (no live billing)

Premium content is unlocked by a signed code. To issue one for a workshop attendee or a manual sale:

```bash
export ENTITLEMENT_SECRET="$(python -c 'import secrets;print(secrets.token_urlsafe(32))')"
python scripts/issue_access_code.py student@example.ac.uk student 30
```

- With no `ENTITLEMENT_SECRET` set, all premium content stays locked (fail closed).
- `src/payments.py` is a provider-agnostic scaffold: webhook signature and replay checks, idempotent event handling, a SQLite entitlement store. It is not connected to any payment provider. See [docs/MONETISATION.md](docs/MONETISATION.md).
- Important: premium prompt text lives in this repository. If the repo is public, anyone can read it. Keep the repository private, or move premium content to a private store, before charging.

## Project layout

```
src/app.py            Home: prompt analyser
src/pages/            Practice, Library, Account, Learn pages
src/analysis.py       prompt analysis logic
src/db.py             SQLite / Postgres layer
src/accounts.py       accounts, sessions, student verification
src/billing.py        Stripe / Lemon Squeezy / PayPal adapters
src/learning.py       modules and grading
data/modules/         learning modules (JSON)
docs/                 PAYMENTS, ARCHITECTURE, PRIVACY and TERMS drafts
src/practice.py       Rubric scoring engine
src/library.py        Search and filtering
src/entitlements.py   Signed access codes
src/payments.py       Webhook and entitlement scaffold
prompts/              Prompt library (JSON, one file per prompt)
data/exercises.json   Practice exercises
docs/                 Schema, deployment runbook, integrity policy, archived reports
tests/                pytest suite
```

## Deployment

`render.yaml` and the `Dockerfile` are configured conservatively: free plan and manual deploys, so merging code never deploys or charges by itself. See [docs/DEPLOYMENT_RUNBOOK.md](docs/DEPLOYMENT_RUNBOOK.md). Set `ENTITLEMENT_SECRET` in the host dashboard, never in git.

## Responsible use

See [docs/ACADEMIC_INTEGRITY.md](docs/ACADEMIC_INTEGRITY.md). Students must follow their institution's AI policy. Prompts about legal, health or financial topics give general information, not professional advice.

## Prompt schema

See [docs/SCHEMA_V2_SPECIFICATION.md](docs/SCHEMA_V2_SPECIFICATION.md). Student Success prompts add `access` (`free` or `premium`), `audience`, `example_input` and `integrity_note`.
