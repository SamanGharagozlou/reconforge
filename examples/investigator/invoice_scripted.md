# ReconForge investigator

Case: `case_invoice_deduction_001`

Mode: **scripted_offline**.
Scripted simulation with real MCP calls. No language model or paid API was used.

Contract checks: **passed**. Priority quality: **not evaluated**.
Financial facts and wording below come from deterministic rules.
The investigator chooses evidence reads and the order of follow-up items.

## Verified financial findings

- f_001: Supplied ledger records total EUR 115,300.00.
- f_002: Supplied provider records total EUR 115,050.00.
- f_003: Supplied bank records total EUR 115,050.00.
- f_004: Ledger minus provider: EUR 250.00; status: needs_review.
- f_005: Provider minus bank: EUR 0.00; status: balanced_by_total.
- f_006: A provider event of EUR -250.00 is absent from the supplied ledger extract.

## Possible explanations — all unverified

1. An import, extraction, or recording difference could explain the ledger/provider mismatch; its cause is unverified.

## Questions in proposed order

1. Are the supplied ledger, provider, and bank extracts complete for this batch?
2. Why do the supplied ledger and provider events differ?

## Human next steps in proposed order

1. Obtain or confirm the complete source reports and reporting cutoffs for this batch.
2. Inspect the original ledger records and import history for the cited event differences.

## Execution trace

- Turn 1: `get_evidence` — `ev_19d9e8d6a6dc76a2bbbe9976bf1c2a39ca193f50065f9e8d143934e0ccc7e74b`
- Turn 2: `get_evidence` — `ev_6515cd141cb91f62b9bc1bb14a7f0da503a7f4cac515a564388e370e12a6da87`
- Turn 3: `submit_investigation`

Conclusion: `cause_undetermined`.
External completeness remains unverified. No financial action is authorized.

Case version: `60ad64451f91f9098218b5d745b46d4eb458e28f10ada3672fb8354eecee3424`

Report ID: `9ab3399e42b165579572eb7f046e31fa87ad161a7e82e134194f613847689823`
