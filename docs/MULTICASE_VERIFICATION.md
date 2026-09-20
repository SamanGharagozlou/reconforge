# Multiple-case verification

Date: 18 September 2026. Implementation: 0.0.3.
Build environment: Python 3.12.14 on Linux with the existing pinned requirements.

Historical milestone. See [report verification](REPORT_VERIFICATION.md) for 0.0.4.

## Observed build results

- All 48 unit and integration tests pass. These include the original 13 financial
  tests and real MCP subprocess connections for both cases.
- The first example still reports a EUR 250.00 ledger-to-provider residual and
  a zero provider-to-bank residual.
- The second example reports matching EUR 82,000.00 ledger/provider totals and
  a EUR 81,850.00 bank payout: zero ledger residual and EUR 150.00 bank residual.
- HTTP and MCP list responses expose both residuals. Both cases require review.
- Evidence requests reject an ID from a different case and reject mismatched
  case versions. Identical bytes can appear in two case contexts without mixing
  the returned case ID or version.
- Editing one fixture leaves previously captured evidence unchanged and changes
  only that case's version on reload.
- The first case retains version
  `60ad64451f91f9098218b5d745b46d4eb458e28f10ada3672fb8354eecee3424`.

## Platform status

On 19 September, the user supplied successful macOS output from the 0.0.3 bank
MCP demonstration. A GitHub Actions screenshot also showed a successful tests
workflow on `feat/multiple-cases`, commit `722daca`. The screenshot did not show
the test count or confirm a merge to `main`. These observations apply to the
0.0.3 milestone, not to later patches.

## Remaining limits

Both cases use synthetic, normalized EUR files with one bank payout per case.
These tests do not establish production-provider compatibility, security
certification, tenant access control, external completeness or a root cause for
the bank discrepancy. There are no LLM agents, persistence or financial actions.
