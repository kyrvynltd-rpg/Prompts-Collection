# Data retention schedule

| Data | Kept for | How it goes |
|---|---|---|
| Account (email, name, scores, favourites, saved prompts) | Until the user deletes the account | Account page, or `delete_account` |
| Sessions | 14 days, or sign out | purge job |
| One-time email codes | 24 h (reset: 1 h), deleted once used | purge job |
| Failed/successful login attempts | 30 days (`RETAIN_LOGIN_ATTEMPT_DAYS`) | purge job |
| Audit log | 12 months (`RETAIN_AUDIT_DAYS`) | purge job |
| Payment event ids (de-duplication) | 24 months (`RETAIN_EVENT_DAYS`) | purge job |
| AI usage counters | 13 months (`RETAIN_AI_USAGE_DAYS`) | purge job |
| Payment records at Stripe/Lemon Squeezy/PayPal | Per provider and UK tax rules (usually 6 years) | Provider |

Run `python scripts/purge.py` daily (Render cron job or any scheduler). Change a period with the env variable. Review this table yearly.
