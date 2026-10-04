# Monetisation plan

Status: code is built and tested with mocks. Nothing is connected to a live payment provider. Figures below are hypotheses to test, not proven demand.

## Tiers
| Tier | Price | For |
|---|---|---|
| Free | 0 | Acquisition and trust: analyser, Practice, free prompts, module 1 |
| Plus | 4.99 GBP/month or 39.99 GBP/year | Full library, all Student Success prompts, modules 1-4, saved progress |
| Pro | 9.99 GBP/month or 99.99 GBP/year | Plus, workspace and templates, AI feedback (monthly cap), advanced track |
| Workshops | by arrangement | Facilitated prompt-literacy sessions; attendees get a workshop access code (grants Pro) |

Prices are configuration (`PRICE_<TIER>_<PERIOD>_GBP`) and must match the price set in the payment provider.

## Competitor reference (checked 3 Oct 2026, re-check before relying on it)
Learn Prompting Plus about USD 21/month billed annually; a Lovable-built prompt library USD 4.99/month; The Prompt Center USD 500/year per campus. Sources: learnprompting.org/pricing, thepromptcenter.com, aipromptlibary.lovable.app/pricing.

## How access works
1. A signed-in user pays through the provider's hosted checkout (link carries their user id).
2. The provider calls the webhook service, which verifies the signature and grants or revokes the tier once per event.
3. Access codes remain available for workshops and vouchers (`scripts/issue_access_code.py`).
Details: [PAYMENTS.md](PAYMENTS.md).

## Before charging anyone
- Keep the repository private (premium text is in it).
- Solicitor review of [TERMS.md](TERMS.md) and [PRIVACY.md](PRIVACY.md); register with the ICO; confirm VAT position.
- Assign copyright to Kyrvyn Ltd in writing ([OWNERSHIP.md](OWNERSHIP.md)).
- Create provider products and links, test in the provider's test mode, then switch to live.
- Choose an email provider so verification and reset emails are delivered.
- Check the owner-action list in [COMPLIANCE_GAP_REVIEW.md](COMPLIANCE_GAP_REVIEW.md).
