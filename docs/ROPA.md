# Record of processing activities (UK GDPR Art 30) - template filled from the code. Owner to confirm.

Controller: Kyrvyn Ltd, https://kyrvynltd.co.uk, company number 17246800. Contact: info@kyrvynltd.co.uk. DPO: not required [confirm].

| Activity | Data | People | Purpose and basis | Recipients | Retention | Security |
|---|---|---|---|---|---|---|
| Accounts | email, name, password hash, terms acceptance | users | run the service (contract) | hosting, database provider, email provider | until account deleted | scrypt, access control, audit log |
| Student verification | university email domain, verified date | students | student eligibility (contract) | email provider | until account deleted | single-use hashed codes |
| Learning progress | exercise ids, scores, attempts | users | deliver the service (contract) | database provider | until account deleted | per-user scoping |
| Workspace (Pro) | saved prompts, tags | Pro users | deliver the service (contract) | database provider | until deleted by user | per-user scoping |
| Payments | customer reference, plan, renewal date | paying users | take payment, tax (contract, legal obligation) | Stripe / Lemon Squeezy / PayPal | per provider, tax rules | signature-verified webhooks |
| AI feedback (Pro) | prompt text sent, usage count | Pro users | deliver feature (contract) | AI provider [name] | text not stored; count 13 months | capped, off by default |
| Security logging | event, user id, time, hashed identifier | users | security (legitimate interests) | log host | 12 months | no secrets or raw emails |
