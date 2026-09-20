# ReconForge investigation report

Case: `case_invoice_deduction_001`

Prepared by deterministic rules. No model calls were used.
Review required: **true**.
Verification: passed against captured rows and fixed report rules.

## Evidenced facts

- **f_001**: Supplied ledger records total EUR 115,300.00. [C1]
- **f_002**: Supplied provider records total EUR 115,050.00. [C2]
- **f_003**: Supplied bank records total EUR 115,050.00. [C3] [C4]
- **f_004**: Ledger minus provider: EUR 250.00; status: needs_review. [C1] [C2]
- **f_005**: Provider minus bank: EUR 0.00; status: balanced_by_total. [C2] [C3] [C4]
- **f_006**: A provider event of EUR -250.00 is absent from the supplied ledger extract. [C1] [C5]
  Event ID: "evt\_invoice\_001"

## Possible explanations — unverified

- An import, extraction, or recording difference could explain the ledger/provider mismatch; its cause is unverified.

## Unresolved questions

- Are the supplied ledger, provider, and bank extracts complete for this batch?
- Why do the supplied ledger and provider events differ?

## Next steps for a human analyst

1. Obtain or confirm the complete source reports and reporting cutoffs for this batch.
2. Inspect the original ledger records and import history for the cited event differences.

## Evidence references

- **C1**: `ledger_events.csv`, captured snapshot of 6 data records.
  SHA-256: `bdb06bf74633b74a443128ec9d329f601d1e9656c27374a4f94cc0e815f106c3`
- **C2**: `psp_events.csv`, captured snapshot of 7 data records.
  SHA-256: `f50c1ae819786b735dddf6eb59e025c9f79879ac84bb922906e27038f5dd1cc2`
- **C3**: `bank_entries.csv`, captured snapshot of 1 data record.
  SHA-256: `dc0189f4c2fcfd4be8742000bb7ed37df828d76e0d3656eb372be5f91bbee306`
- **C4**: `bank_entries.csv`, data record 1; evidence `ev_19d9e8d6a6dc76a2bbbe9976bf1c2a39ca193f50065f9e8d143934e0ccc7e74b`.
  SHA-256: `dc0189f4c2fcfd4be8742000bb7ed37df828d76e0d3656eb372be5f91bbee306`
- **C5**: `psp_events.csv`, data record 7; evidence `ev_6515cd141cb91f62b9bc1bb14a7f0da503a7f4cac515a564388e370e12a6da87`.
  SHA-256: `f50c1ae819786b735dddf6eb59e025c9f79879ac84bb922906e27038f5dd1cc2`

Case version: `60ad64451f91f9098218b5d745b46d4eb458e28f10ada3672fb8354eecee3424`

Report ID: `9ab3399e42b165579572eb7f046e31fa87ad161a7e82e134194f613847689823`

Synthetic data only. External completeness is unverified. Hashes identify captured bytes; they do not establish trusted provenance. This report authorizes no financial action.
