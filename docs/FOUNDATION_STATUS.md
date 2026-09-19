# Foundation verification

Historical 0.0.2 record. See [current verification](MULTICASE_VERIFICATION.md)
for the later confirmation of CI and the multiple-case implementation.

Date: 18 September 2026. Implementation version: 0.0.2.
Environment tested: Python 3.12.14 on Linux.

## Observed results

- `python3 -m reconforge.demo` completes successfully.
- Ledger total: EUR 115,300.00.
- Provider component total: EUR 115,050.00.
- Bank payout total: EUR 115,050.00.
- The result identifies `evt_invoice_001` as absent from the ledger.
- The provider source reference identifies data record 7 and the file hash.
- With the pinned environment installed, `python -m unittest discover -s tests -v`
  passes all 33 tests, including the original 13 financial checks.
- `python -m reconforge.mcp_demo` discovers the three MCP tools over a real stdio
  subprocess connection and retrieves the case and matching evidence.
- The FastAPI contract is checked using its ASGI test client: typed case output,
  exact evidence, stale-version errors, unknown IDs, and rejected write methods.
- `python -m pip check` reports no broken requirements.

The tests cover exact money parsing, invalid representations, formatting,
the expected fixture, source references, duplicates, unsupported currency,
source scope mismatch, missing bank records, separate residuals, offsetting
event changes, completeness limitations and timezone requirements. New checks
cover stable captured evidence after file edits, frozen case values, input bounds,
case versions, transport money types, HTTP errors, MCP schemas and tool discovery.

The original 13-test baseline passed on macOS and GitHub Actions on
17 September 2026. On 18 September, the expanded 33-test suite and
MCP demonstration also passed on macOS with Python 3.12.
Verification of the expanded suite on GitHub Actions is pending.

## Remaining work

This is the financial baseline for the proposed project. It has not been tested
against real customer data and is not a production adapter or security system.
A read-only local MCP server and case API are now implemented. LLM agents,
identity, persistence and approvals remain planned. This milestone does not
establish production readiness, real-provider compatibility, or tenant isolation.
