# ReconForge investigation report

Case: `case_bank_shortfall_001`

Prepared by deterministic rules. No model calls were used.
Review required: **true**.
Verification: passed against captured rows and fixed report rules.

## Evidenced facts

- **f_001**: Supplied ledger records total EUR 82,000.00. [C1]
- **f_002**: Supplied provider records total EUR 82,000.00. [C2]
- **f_003**: Supplied bank records total EUR 81,850.00. [C3] [C4]
- **f_004**: Ledger minus provider: EUR 0.00; status: balanced_on_supplied_events. [C1] [C2]
- **f_005**: Provider minus bank: EUR 150.00; status: needs_review. [C2] [C3] [C4]

## Possible explanations — unverified

- Different reporting cutoffs or incomplete payout reporting could explain the bank difference; this is unverified.
- An unreported adjustment or an error in a supplied source could explain the bank difference; this is unverified.

## Unresolved questions

- Are the supplied ledger, provider, and bank extracts complete for this batch?
- What explains the provider-to-bank difference? The supplied records do not establish its cause.

## Next steps for a human analyst

1. Obtain or confirm the complete source reports and reporting cutoffs for this batch.
2. Compare the provider payout advice and complete bank statement, including dates and any separately reported deductions.

## Evidence references

- **C1**: `ledger_events.csv`, captured snapshot of 3 data records.
  SHA-256: `31b729639e04d959f5b881f01be3bf7dc9d8cc95041808f39bc6e801f02d7b25`
- **C2**: `psp_events.csv`, captured snapshot of 3 data records.
  SHA-256: `31b729639e04d959f5b881f01be3bf7dc9d8cc95041808f39bc6e801f02d7b25`
- **C3**: `bank_entries.csv`, captured snapshot of 1 data record.
  SHA-256: `1a3053671a3f8da2c2de026e6f24b2d7024d1d35087efed99bc586a75310ef6b`
- **C4**: `bank_entries.csv`, data record 1; evidence `ev_599d46a4db64b51d7af13acfb4892fb37c1c74378171eda4ba41cb3c5b6c0496`.
  SHA-256: `1a3053671a3f8da2c2de026e6f24b2d7024d1d35087efed99bc586a75310ef6b`

Case version: `40c7cf43fdc238057dae1ebc1b6a4e28a7e50d9f5035417f7c81b74c704612d3`

Report ID: `444285163aec8aa1b736d1cbd64c0387432107ac367345411d704bef215b366c`

Synthetic data only. External completeness is unverified. Hashes identify captured bytes; they do not establish trusted provenance. This report authorizes no financial action.
