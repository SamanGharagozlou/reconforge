# Bounded-investigator verification

> Historical v0.0.5 verification record. For v0.0.6 Anthropic live acceptance, see [Anthropic live-provider verification](ANTHROPIC_VERIFICATION.md).

Date: 25 September 2026. Implementation: 0.0.5.
Latest local verification: macOS, Python 3.12.9. Build-environment verification also passed on Python 3.12.14 on Linux.

## Scope of observed checks

The suite has **110 tests**: the preceding 75 and 35 investigator/adapter tests.
It exercises the contract, actual local MCP subprocesses, and mocked provider
HTTP responses. It does not call a live language model.

| Scenario | Required row reads | Scripted turns | Ledger / bank residual |
| --- | ---: | ---: | --- |
| Missing invoice deduction | 2 | 3 | EUR 250.00 / EUR 0.00 |
| Bank shortfall | 1 | 2 | EUR 0.00 / EUR 150.00 |

Both scripted runs preserve `cause_undetermined` and report zero provider
requests. The balanced-record contract test retains the external-completeness
question without inventing a discrepancy hypothesis.

| Failure tested | Expected outcome |
| --- | --- |
| Changed, coerced, missing, duplicated, or invented findings | Reject proposal |
| Invented, cross-case, unread, duplicated, or substituted citations | Reject request or proposal |
| Changed case/version/report identity | Reject |
| Added cause, free-form diagnosis, or financial-action fields | Reject |
| Omitted unknowns or inapplicable playbook codes | Reject |
| Unsupported tool, URL, or model-controlled case arguments | Block before MCP dispatch |
| Repeated read, excess reads/turns, oversized input | Stop within host bounds |
| Provider refusal, free text, multiple calls, or ambiguous JSON | Reject |
| HTTP errors, redirects, timeout, malformed/oversized response | Stop; no automatic retries |
| Provider error body containing dummy secret/source text | Keep it out of the displayed error |
| Source description resembling an instruction | Omit the description from model payloads |
| Nested MCP shutdown error | Preserve a single sanitized contract error |

The mock HTTP loop checks usage accounting, mode labels, context replay, the
fixed endpoint, and request configuration. A passing mock does not establish
that a real model accepts the request schema or makes good decisions.

## Acceptance status

| Gate | Status |
| --- | --- |
| Linux offline tests and both MCP scenarios | Passed in the build environment |
| macOS 0.0.5 full offline suite | Passed on 25 September 2026: 110 tests in 2.738s; `pip check` clean |
| macOS scripted investigator demos | Passed for bank-shortfall and invoice-deduction cases |
| GitHub Actions for the 0.0.5 branch | Pending publication |
| Live API schema/model acceptance | Attempted; stopped at HTTP 429 before an accepted run |
| Live model priority-quality evaluation | Not established |

On 25 September 2026, the local macOS v0.0.5 working tree passed all 110
offline tests in 2.738 seconds with no broken requirements. Both bundled
investigator scenarios also completed in `scripted_offline` mode with their
contract checks passing. These scripted runs are not live model evidence.

A live OpenAI attempt was made separately and stopped with HTTP 429. Because
the current adapter intentionally redacts provider error bodies, that result
does not distinguish quota, spend-limit, billing-credit, or rate-limit causes
and does not establish successful live schema/model acceptance.

No production readiness, tenant authorization, source authenticity, external
completeness, causal diagnosis, or model-priority quality is established.
