# Monetisation plan (scaffold only, nothing is live)

## Offer hypotheses (to test, not proven)
- Free: analyser, Practice mode, 6 Student Success prompts. Purpose: acquisition and trust.
- Premium (about GBP 1/month idea): 9 premium Student Success prompts plus new content each month.
- Workshops: facilitated prompt-literacy session using Practice mode, with a workshop access code for attendees.

Competitor prices checked 3 Oct 2026: Learn Prompting Plus about USD 21/month billed annually, a Lovable-built prompt library USD 4.99/month, The Prompt Center USD 500/year per campus. A GBP 1 price is well below them. Validate demand with a small paid pilot before building more.

## How access works today
1. You issue a signed code with `scripts/issue_access_code.py` (subject, plan, days).
2. The student enters it on the Account page. Verification is local, HMAC-SHA256, expiry enforced, fails closed.

## Path to automatic billing (not built)
1. Pick a provider (a merchant of record such as Paddle or Lemon Squeezy handles UK/EU VAT; Stripe needs you to handle it). Needs an account decision from the owner.
2. Write a provider adapter implementing `PaymentProvider.parse_webhook`.
3. Run a small separate web service (Streamlit cannot receive webhooks) that calls `payments.process_webhook`, then issues a code by email or exposes a lookup.
4. Keep `ENTITLEMENT_SECRET` and `PAYMENT_WEBHOOK_SECRET` in the host's secret store.

## Before charging anyone
- Make the repo private or move premium content out of it.
- Add terms, a privacy notice, and a refund policy; register for data protection if you store student emails.
- Confirm the company (Kyrvyn Ltd) is the contracting party and that IP is assigned to it.
