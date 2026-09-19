# Synthetic bank-payout discrepancy

All records are fictional, normalized ReconForge examples. They do not represent
a production payment-provider report or an actual missing payment.

| Component | Ledger EUR | Provider EUR |
| --- | ---: | ---: |
| Captured payments | 85,000.00 | 85,000.00 |
| Provider fee | -1,000.00 | -1,000.00 |
| Refunds | -2,000.00 | -2,000.00 |
| Total | **82,000.00** | **82,000.00** |

The single supplied bank payout is **EUR 81,850.00**. Therefore:

- Ledger minus provider: EUR 0.00, `balanced_on_supplied_events`.
- Provider minus bank: EUR 150.00, `needs_review`.
- Ledger/provider event differences: none.
- Overall review required: true.
- External reporting completeness verified: false.

The reason for the difference is unknown. A timing difference, withheld amount,
missing report, or data error cannot be established from these files. A reviewer
would need additional payout and bank information before choosing a resolution.
The program does not classify the difference as an invoice deduction or propose
an automatic adjustment.

`expected.json` records manually specified expectations for the tests. Neither
the reconciliation core nor the case store reads it to calculate results.

The bank evidence is `bank_entries.csv`, data record 1, event `evt_bank_001`.
Its amount is EUR 81,850.00, not the EUR 150.00 residual: the residual comes from
comparing the provider components with the bank row. Both source snapshots are
retained in the case. Record numbers exclude the CSV header.

The schema and signed-amount rules are the same as the
[invoice example](../invoice_deduction/README.md). Event IDs may repeat in another
case: lookup uses the selected case, case version and evidence ID together.

```bash
python3 -m reconforge.demo --data-dir examples/bank_shortfall --json
python -m reconforge.mcp_demo --case-id case_bank_shortfall_001
```
