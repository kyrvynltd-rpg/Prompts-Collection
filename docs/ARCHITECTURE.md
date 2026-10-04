# Architecture

```
Streamlit UI (src/app.py, src/pages/*)  ->  session.py  ->  accounts / learning / billing  ->  db.py  ->  SQLite or Postgres
Payment provider  ->  webhook_server.py  ->  billing.py (verify, normalise, apply once)  ->  grants table
```
- `analysis.py`: prompt analysis logic, no Streamlit, tested.
- `db.py`: one interface, SQLite by default, Postgres when `DATABASE_URL` is set. Numbered migrations.
- `accounts.py`: scrypt passwords, hashed session and email tokens, lockout after 5 failures in 15 minutes, student verification (.ac.uk), data export and deletion.
- `learning.py` and `data/modules/*.json`: lessons, exercises and local deterministic grading. Add a module by adding a JSON file.
- `billing.py`: provider adapters, entitlements, checkout links. `entitlements.py`: signed access codes for workshops.

## Database choice
- Development: SQLite file, no setup.
- Production: Supabase or Neon Postgres, free tier first (about 500 MB, plenty for this). Use the pooled connection string as `DATABASE_URL`. Supabase is used only as Postgres here, not for its auth, so there is no lock-in.
- Streamlit sessions: the sign-in lives in browser session state, so a page refresh signs the learner out. Fixing that needs a different front end or a cookie component. It is the main UX limit of Streamlit.
