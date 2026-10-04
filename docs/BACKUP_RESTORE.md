# Backup and restore

- **Postgres (production):** turn on the provider's automated daily backups and point-in-time recovery (Supabase and Neon both offer this; check the plan). Keep at least 7 days.
- **SQLite (small deployments):** `python scripts/backup.py /path/to/backups` writes a consistent copy with owner-only permissions. Copy it off the machine (encrypted storage).
- **Restore test, every quarter:** restore the latest backup into a new database, point a staging copy at it, sign in, check progress and grants. Record the date and result.
- **Erasure and backups:** a deleted account can remain in backups until they expire (up to the backup age). State this in the privacy policy [done in PRIVACY.md draft, confirm wording].
- **Secrets are not in the database.** Rotate them in the host's environment settings.
