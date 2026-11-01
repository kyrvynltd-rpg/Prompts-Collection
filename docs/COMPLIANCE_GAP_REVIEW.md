# Compliance gap review: UK GDPR and ISO 27001-style controls

Status: **aligned with** these frameworks in the code and documents. This is **not** a certification and not legal advice. ISO/IEC 27001 certifies an organisation's management system through an accredited auditor. UK GDPR compliance depends on how Kyrvyn Ltd operates the service. Items marked OWNER need a person or a provider account, not code.

Legend: Done = in code/docs on this branch. Partial = built, needs configuration or an owner decision. Open = not done.

## UK GDPR
| Requirement | Status | Evidence / gap |
|---|---|---|
| Lawful basis, transparency (Arts 5, 6, 13) | Partial | docs/PRIVACY.md draft lists data, purposes, bases, recipients, transfers, retention, rights and cookies. OWNER: solicitor review, fill brackets. |
| Consent to terms recorded | Done | `users.terms_accepted_at`, `terms_version` stored at sign-up. |
| Data minimisation | Done | Only email, optional name, scores, saved prompts. Exercise text is graded, not stored. Card data never touches the app. |
| Access and portability (Arts 15, 20) | Done | Account page "Download my data" (JSON, includes workspace prompts). |
| Erasure (Art 17) | Done | "Delete my account" removes sessions, tokens, progress, favourites, workspace prompts, AI usage, grants and customer links; email is anonymised. Cancel the subscription in the payment provider as well. |
| Rectification (Art 16) | Open | No edit-profile page yet (name/email change). |
| Storage limitation | Done | `src/retention.py`, `scripts/purge.py`, docs/DATA_RETENTION.md. OWNER: schedule it daily. |
| Security of processing (Art 32) | Partial | See ISO table. |
| Breach handling (Arts 33, 34) | Partial | docs/INCIDENT_RESPONSE.md (72 hour ICO rule). OWNER: name the responsible person. |
| Records of processing (Art 30) | Done | docs/ROPA.md (template filled from the code). OWNER: confirm. |
| Processors and transfers (Arts 28, 44+) | Open | docs/SUBPROCESSORS.md lists likely processors. OWNER: sign DPAs, confirm transfer safeguards (UK IDTA / UK Addendum). |
| ICO registration | Open | OWNER: register Kyrvyn Ltd and pay the data protection fee. |
| DPIA | Not required on current scope | Low-risk processing. Revisit if AI feedback usage or children's data grows. |
| Children | Open | Terms say 16+ [SOLICITOR TO CONFIRM: minimum age]. No age gate in code. |

## ISO 27001 Annex A-style controls (code and operations)
| Control area | Status | Evidence / gap |
|---|---|---|
| Access control, authentication (A.5.15-5.18, 8.5) | Done | scrypt password hashes, lockout (5 fails / 15 min), 14 day sessions, sign out everywhere on password reset, common-password rejection, password reset by emailed one-time code, email confirmation. Open: no MFA, no admin role UI. |
| Least privilege | Done | Every database query is scoped to the signed-in user id (tested: workspace isolation, code reuse across users). Webhook service holds only provider secrets. |
| Secrets management (A.8.24) | Done | Secrets only from environment. CI scans for committed secrets. `.env` is git-ignored. OWNER: use Render environment secrets, rotate on staff change. |
| Cryptography | Done | scrypt, SHA-256 token hashing, HMAC webhook verification, constant-time compares. TLS is provided by the host (OWNER: force HTTPS). |
| Logging and monitoring (A.8.15, 8.16) | Done | `audit_log` table plus `audit` logger: register, login ok/fail/locked, logout, reset, verification, export, delete, payment events, rejected webhooks, AI use. No passwords, tokens or raw emails logged. Open: alerting on spikes (OWNER: log drain + alert). |
| Backup (A.8.13) | Partial | `scripts/backup.py` (SQLite) and docs/BACKUP_RESTORE.md. OWNER: enable Postgres provider backups and test a restore. |
| Retention and disposal (A.8.10) | Done | See GDPR. |
| Secure development (A.8.25-8.29) | Done | CI: ruff, mypy, 95% coverage floor, secret scan, pip-audit, Dependabot. Branch-protection requirement is OWNER (GitHub setting). |
| Supplier security (A.5.19-5.23) | Open | docs/SUBPROCESSORS.md. OWNER: review each supplier. |
| Incident management (A.5.24-5.27) | Partial | docs/INCIDENT_RESPONSE.md. OWNER: assign roles and rehearse once. |
| Business continuity | Partial | Backups and restore doc. Free-tier hosting has no uptime guarantee. |
| Asset and risk management, ISMS, internal audit, management review | Open | Organisational. OWNER, outside code. Needed for any certification. |
| HR, physical and endpoint security | Open | Organisational. |
| Vulnerability disclosure | Done | SECURITY.md (info@kyrvynltd.co.uk). |

## Known technical limits
- Streamlit keeps the sign-in in the browser session only. A refresh signs the user out.
- Postgres and payment paths have been tested only against mocks and SQLite.
- No rate limiting on the webhook endpoint beyond signature checks and body size. Put the host's rate limiting in front.
- Email delivery is not wired yet (console stub), so reset and verification codes are not sent until an email provider is added.
