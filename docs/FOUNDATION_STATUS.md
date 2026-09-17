# Foundation verification

Date: 17 September 2026.
Environment tested: Python 3.12.14 on Linux.

## Observed results

- `python3 -m reconforge.demo` completes successfully.
- Ledger total: EUR 115,300.00.
- Provider component total: EUR 115,050.00.
- Bank payout total: EUR 115,050.00.
- The result identifies `evt_invoice_001` as absent from the ledger.
- The provider source reference identifies data record 7 and the file hash.
- `python3 -m unittest discover -s tests -v` passes all 13 tests.

The tests cover exact money parsing, invalid representations, formatting,
the expected fixture, source references, duplicates, unsupported currency,
source scope mismatch, missing bank records, separate residuals, offsetting
event changes, completeness limitations and timezone requirements.

## Remaining work

This is the financial baseline for the proposed project. It has not been tested
against real customer data and is not a production adapter or security system.
MCP, agents, a case API, identity, persistence and approvals remain planned.
macOS setup still needs verification on the user's machine.
