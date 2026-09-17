# First workflow scope

User: a payment operations analyst checking a settlement discrepancy.

Input: normalized, synthetic provider, ledger, and bank CSVs for one batch.

Output tonight: exact totals, residuals, event differences, and source references.

Target output for the later demonstration: a source-backed investigation,
proposed next action, and a version-bound human-review decision.

## Initial case catalogue

| Case | Expected behaviour | Current status |
| --- | --- | --- |
| Invoice deduction absent from ledger | Identify event and EUR 250 residual | Demonstrated |
| Duplicate imported event | Reject the input | Tested within a file |
| Bank payout differs from provider | Report provider-to-bank residual | Tested |
| Missing bank data | Stop with an explicit input error | Tested |
| Offset event changes with equal totals | Require review despite zero net difference | Tested |
| Partial refund | Model separate linked financial events | Planned |
| Payout timing difference | Consider effective time and reporting completeness | Planned |
| Ambiguous cross-system references | Return candidates and withhold a match | Planned |

## First demonstration acceptance criteria

1. Ledger total is 11,530,000 cents.
2. Provider component total is 11,505,000 cents.
3. Bank payout total is 11,505,000 cents.
4. Ledger-to-provider residual is 25,000 cents.
5. Provider-to-bank residual is zero.
6. The missing ledger event has the ID `evt_invoice_001`.
7. Evidence identifies the provider source record and its file hash.
8. The case requires review; the program cannot approve or post anything.

## Explicit limits

The starter has no MCP, language model, user authentication, database, durable
worker, payment integration, or automated accounting action. It compares fixture
IDs that already match across two normalized sources. Real adapter semantics,
record completeness and cross-system identity resolution are future work.

## First issues to create

- Domain: typed case object carrying residuals and evidence IDs.
- API: read a single synthetic case through a documented endpoint.
- Evidence: return bounded source rows by verified fixture reference.
- MCP: expose that read operation as a typed tool.
- Evaluation: distinguish supported facts, proposed explanations, and unknowns.
