# Synthetic invoice-deduction example

All names, IDs, amounts and events are fictional and generated for this project.
These are ReconForge normalized fixture files, not actual Adyen report files.

## Source interpretation

`psp_events.csv` contains settlement components. Captures add to the settlement;
fees, refunds, this reserve increase, and the invoice deduction reduce it. The
payout transfer itself is deliberately excluded from these components so it is
not counted twice.

`ledger_events.csv` is an operational extract of expected settlement components,
not a double-entry accounting ledger. It intentionally omits the invoice deduction.

`bank_entries.csv` contains the single received payout for this batch.

| Component | Ledger EUR | Provider EUR |
| --- | ---: | ---: |
| Three captured amounts | 120,000.00 | 120,000.00 |
| Fee | -1,200.00 | -1,200.00 |
| Refund | -2,500.00 | -2,500.00 |
| Reserve increase | -1,000.00 | -1,000.00 |
| Invoice deduction | Absent | -250.00 |
| Total | **115,300.00** | **115,050.00** |

The bank received EUR 115,050.00.

## Schema

Each CSV has the same ordered headers:

`tenant_id, merchant_id, batch_id, event_id, event_type, amount_eur, currency,
effective_at, description`.

- The scope is one tenant, merchant, batch and EUR currency per run.
- Amounts are signed decimal strings with exactly two decimal places.
- The comparison uses canonical event IDs shared by these normalized fixtures.
- Event IDs are unique within each file; the same ID across sources refers to
  the same financial event for this demonstration.
- Captures and payouts are positive. Fees, refunds and invoice deductions are
  negative in this restricted schema. Reserve adjustments may have either sign.
- This does not cover all directions or variants of real financial journal types.
- Timestamps must include a timezone and represent business-effective time.
- Descriptions are untrusted data and are never executed.

Evidence `record_number` starts at 1 for the first data record and excludes the
header. The invoice deduction is data record 7, physical line 8 in this file.
CSV records with quoted newlines may span multiple physical lines.

`expected.json` is the independent expected result. The demo does not read it to
compute the output; tests use it to check the arithmetic and expected finding.

This controlled example has known synthetic contents. Completeness of an arbitrary
real source cannot be inferred from matching totals or a file hash.
