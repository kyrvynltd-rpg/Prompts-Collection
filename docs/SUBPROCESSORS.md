# Suppliers and processors (confirm each, sign a data processing agreement, check transfers)

| Supplier | Purpose | Data | Status |
|---|---|---|---|
| Render (or chosen host) | Hosting | all app data in transit | [to confirm] |
| Supabase / Neon | Postgres | all stored data | [to confirm] |
| Stripe / Lemon Squeezy / PayPal | Payments | email, customer reference, plan | [to confirm which are used] |
| Email provider (Resend, Postmark, SES) | Verification and reset emails | email address | [not chosen] |
| AI provider | Pro AI feedback | prompt text only | [not chosen, off by default] |
| GitHub | Code hosting | no customer data | private repository |
