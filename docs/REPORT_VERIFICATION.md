# Investigation-report verification

Date: 20 September 2026. Implementation: 0.0.4.
Build environment: Python 3.12.14 on Linux with the existing pinned requirements.

Historical milestone. Current results are in [investigator verification](INVESTIGATOR_VERIFICATION.md).

## Observed build results

All **75 unit and integration tests pass**: the previous 48 plus 27 report tests.
The suite includes real MCP stdio subprocess connections for both reports and
the existing case/evidence tools. HTTP report responses are checked through the
application's test client.

| Scenario | Ledger residual | Bank residual | Findings | Citation occurrences |
| --- | ---: | ---: | ---: | ---: |
| Invoice deduction | EUR 250.00 | EUR 0.00 | 6 | 11 |
| Bank shortfall | EUR 0.00 | EUR 150.00 | 5 | 9 |

Citation occurrences count every citation attached to a finding. The Markdown
reference list deduplicates them. Both cases require review and retain their
0.0.3 case versions. The bank report labels its possible explanations as
unverified and retains an explicit unknown-cause question.

The new tests cover:

- Altered amounts, non-integer money values, and unsupported statements.
- Invented, cross-case, stale, mismatched, and existing-but-irrelevant citations.
- Missing findings, duplicate finding IDs, and omitted completeness questions.
- Hypotheses promoted to facts and requests to post a financial adjustment.
- Forged review, completeness, or financial-action flags.
- Inconsistent case totals and omitted case differences, detected by recomputing
  facts from captured source rows.
- Changed source versions, frozen snapshots, zero net differences that still
  require review, and balanced records with unverified completeness.
- Source descriptions resembling instructions, escaped event identifiers, and
  an explicit error above the report's 100-event-difference limit.
- HTTP and MCP error behaviour for missing, unknown, and stale case context.

## Platform status

On 20 September, the user reported the 0.0.4 checks succeeded, the pull request
was merged after its checks passed, and the local `main` checkout was synced and
working. These are user-reported macOS/GitHub outcomes; the build-environment
results above were observed directly. Neither establishes a later version's status.

## What verification does not establish

The accepted report grammar is fixed. The tests do not evaluate model quality,
arbitrary natural-language fact checking, prompt-injection resistance of an LLM,
production-provider compatibility, tenant access control, or deployment security.
The source-text test establishes that descriptions are not promoted into the
deterministic report. Captured file hashes and report digests do not prove source
authenticity. No external completeness, causal explanation, accounting approval,
or financial action is certified.
