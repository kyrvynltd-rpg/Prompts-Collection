# Security incident response

**Owner:** [name, role, phone] (Kyrvyn Ltd). Backup: [name].

1. **Detect.** Sources: audit log spikes (many `login_fail`, `login_locked`, `webhook_rejected`), provider alerts, user reports to the security mailbox.
2. **Triage (within 4 hours).** What happened, which data, how many people, is it still going on. Write it down with times.
3. **Contain.** Rotate affected secrets (ENTITLEMENT_SECRET, webhook secrets, API keys, database password). Revoke sessions: `DELETE FROM sessions`. Disable a provider by clearing its link/secret env vars. Take the app offline if needed.
4. **Assess.** Personal data involved and risk to people (UK GDPR). If it is a notifiable breach, **tell the ICO within 72 hours of becoming aware** (ico.org.uk). If the risk to people is high, tell them without undue delay.
5. **Recover.** Fix the cause, restore from backup if needed (docs/BACKUP_RESTORE.md), watch the audit log.
6. **Learn.** Within 14 days: short written review, actions with owners, update these docs. Keep a breach log even when no notification is needed.

Contacts: ICO breach line and web form [check current details], payment providers' security contacts, hosting support.
