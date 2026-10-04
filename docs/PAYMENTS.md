# Payments

Tiers: Free, Plus (£4.99/month, £39.99/year) and Pro (£9.99/month, £99.99/year). Change `PRICE_<TIER>_<PERIOD>_GBP` (display) and the price in the provider (the real charge). Both must match.

Plus: all Premium prompts and modules. Pro: Plus, AI prompt feedback (monthly cap, off until `AI_API_KEY` is set), personal workspace with export, advanced track, templates and workshop pack. Workshop access codes grant Pro.

## How it works
1. A signed-in learner clicks "Pay with ..." on the Account page. The link carries their user id (`client_reference_id` for Stripe, custom data `user_id` for Lemon Squeezy, `custom_id` for PayPal).
2. The provider takes payment on its own hosted page. The app never sees card details.
3. The provider calls `POST /webhooks/<provider>` on the webhook service (`src/webhook_server.py`).
4. The adapter in `src/billing.py` checks the signature, turns the event into one normal shape, and grants or revokes access once (duplicate events are ignored).

## Which provider
- Stripe: cheapest card fees for a UK seller, no extra platform fee. You are the seller and handle VAT yourself.
- Lemon Squeezy: merchant of record, so it handles VAT and sales tax for you, at a higher fee. Good if you do not want tax admin.
- PayPal: adds reach, but the webhook check needs an API call. Wire your PayPal credentials into `PayPalProvider(verifier=...)` before use. It fails closed without it.
Start with Stripe or Lemon Squeezy only. Add PayPal later.

## What you need to do (nothing here is done for you)
1. Create a product with a monthly and an annual price. Create a Payment Link (Stripe) or checkout URL (Lemon Squeezy). Make one link per tier and period, and put each in `STRIPE_LINK_PLUS_MONTHLY`, `STRIPE_LINK_PRO_ANNUAL` and so on (see `.env.example`). On each Stripe link set metadata `plan` = `plus` or `pro`. For PayPal the tier travels in `custom_id`.
2. In Stripe, make the link collect subscriptions and send these webhook events: `checkout.session.completed`, `invoice.paid`, `customer.subscription.deleted`, `charge.refunded`. In Lemon Squeezy: subscription created, payment success, expired, order refunded.
3. Deploy the webhook service, set the webhook secrets, point the provider at `https://<host>/webhooks/stripe` (or `lemonsqueezy`).
4. Test in the provider's test mode first. Check a purchase unlocks Premium and a cancellation locks it after the paid period.

## Limits
- Student price needs a second price in the provider. The app records verified students but does not yet pick the price automatically.
- Refund and chargeback events revoke access immediately.
- A 3 day grace period covers late renewals.
