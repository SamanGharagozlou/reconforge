# First workflow scope

User: a payment operations analyst checking a settlement discrepancy.

Input: normalized, synthetic provider, ledger, and bank CSVs for one batch per case.

Current output: exact totals, residuals, event differences, source references,
and immutable case/evidence views exposed through a local API and stdio MCP.

Target output for the later demonstration: a source-backed investigation,
proposed next action, and a version-bound human-review decision.

## Initial case catalogue

| Case | Expected behaviour | Current status |
| --- | --- | --- |
| Invoice deduction absent from ledger | Identify event and EUR 250 residual | Demonstrated |
| Duplicate imported event | Reject the input | Tested within a file |
| Bank payout differs from provider | Report EUR 150 provider-to-bank residual while the ledger matches | Demonstrated as a second case |
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

The prototype has a local read-only API and MCP server. It has no language model,
user authentication, database, durable worker, payment integration, or automated
accounting action. It compares fixture
IDs that already match across two normalized sources. Real adapter semantics,
record completeness and cross-system identity resolution are future work.

## Completed in the Day 1 implementation

- Typed case object carrying residuals, evidence IDs, and a snapshot version.
- Documented HTTP endpoints for the synthetic case and its captured evidence.
- Bounded evidence lookup that rejects unknown IDs and outdated case versions.
- Three typed read-only MCP tools, tested through a real stdio connection.

## Next implementation work

- Add timing, ambiguity and incomplete-data scenarios with explicit expected behaviour.
- Add an investigator that separates supported facts, hypotheses, and unknowns.
- Define evaluation failures before introducing autonomous orchestration.
- Design authentication and tenant access before supporting customer data.

## Completed in the multiple-case increment

- Serve two named synthetic cases through the same HTTP and MCP interfaces.
- Include both residuals in each case summary so bank differences remain visible.
- Keep evidence lookup inside the requested case and its current snapshot version.
- Preserve the first case's calculations, version and evidence identifiers.
- Bound the configured case catalogue to 32 entries and reject invalid startup data.
- Test both scenarios over real MCP stdio connections, with 48 tests in the suite.
