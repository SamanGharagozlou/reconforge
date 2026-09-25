# ReconForge investigator

Case: `case_bank_shortfall_001`

Mode: **scripted_offline**.
Scripted simulation with real MCP calls. No language model or paid API was used.

Contract checks: **passed**. Priority quality: **not evaluated**.
Financial facts and wording below come from deterministic rules.
The investigator chooses evidence reads and the order of follow-up items.

## Verified financial findings

- f_001: Supplied ledger records total EUR 82,000.00.
- f_002: Supplied provider records total EUR 82,000.00.
- f_003: Supplied bank records total EUR 81,850.00.
- f_004: Ledger minus provider: EUR 0.00; status: balanced_on_supplied_events.
- f_005: Provider minus bank: EUR 150.00; status: needs_review.

## Possible explanations — all unverified

1. Different reporting cutoffs or incomplete payout reporting could explain the bank difference; this is unverified.
2. An unreported adjustment or an error in a supplied source could explain the bank difference; this is unverified.

## Questions in proposed order

1. Are the supplied ledger, provider, and bank extracts complete for this batch?
2. What explains the provider-to-bank difference? The supplied records do not establish its cause.

## Human next steps in proposed order

1. Obtain or confirm the complete source reports and reporting cutoffs for this batch.
2. Compare the provider payout advice and complete bank statement, including dates and any separately reported deductions.

## Execution trace

- Turn 1: `get_evidence` — `ev_599d46a4db64b51d7af13acfb4892fb37c1c74378171eda4ba41cb3c5b6c0496`
- Turn 2: `submit_investigation`

Conclusion: `cause_undetermined`.
External completeness remains unverified. No financial action is authorized.

Case version: `40c7cf43fdc238057dae1ebc1b6a4e28a7e50d9f5035417f7c81b74c704612d3`

Report ID: `444285163aec8aa1b736d1cbd64c0387432107ac367345411d704bef215b366c`
