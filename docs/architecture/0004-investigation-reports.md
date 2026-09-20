# ADR 0004: fixed-rule reports verified against captured source rows

Status: implemented in the 0.0.4 local synthetic prototype, 20 September 2026.

## Context

A residual and an evidence ID are useful to a program, but a reviewer also needs
to know what the evidence establishes, what remains unknown, and what records to
inspect next. A model could produce plausible prose with correct-looking
citations while changing an amount, inventing a cause, or omitting a discrepancy.
The first report contract must make those failures explicit and testable.

## Decision

Generate a bounded report with deterministic rules. Its typed sections contain:

- Findings: fixed claim types, exact integer cents where applicable, and citations.
- Hypotheses: fixed possibilities with an `unverified` status and triggering finding IDs.
- Unresolved questions: including external completeness for every report.
- Next steps: information requests assigned to a human analyst.

Every report identifies its case and captured version. Report schema and policy
versions are both `0.1.0`; these are separate from the application's `0.0.4` version.
The report cannot assert external completeness or allow financial actions.

Two citation types have distinct purposes. A row citation identifies one record
with its evidence ID, filename, data record number, event ID, and source hash.
A snapshot citation identifies a whole captured source and its record count.
Totals require snapshots; an event's absence from a supplied extract requires
the compared snapshot as well as the row present in the other source. Absence
from that extract does not establish absence from an external system.

## Verification boundary

`verify_report` receives the expected case ID and version separately from the
candidate. It revalidates even an existing model instance, because a caller can
otherwise construct an unchecked copy. It then:

1. Rejects a stale expected version or a candidate from another case/version.
2. Resolves captured evidence through `CaseStore`, checking scope, identity,
   source hashes, duplicate IDs, and coverage of each captured snapshot.
3. Recomputes exact source totals, both residuals, event differences, and review
   status from captured rows independently of the case's stored calculations.
4. Checks each snapshot or row citation against that evidence context.
5. Requires the entire report to match the permitted report rules, including
   all findings, their particular supporting citations, uncertainty labels,
   questions, and next steps.

The last step uses the same wording rules as the generator. It is a closed-format
conformance check, not an independent judge of arbitrary natural language. The
separate arithmetic and event comparison catch inconsistent case calculations;
tests mutate reports to exercise rejection paths. A plausible new explanation
is not automatically a supported fact.

Only then does the server produce a `VerifiedReport` envelope. Its SHA-256
`report_id` covers canonical JSON of the report, including schema/policy versions
and the case version. It is a content checksum, not a signature, proof of trusted
origin, or authorization token. A caller can construct an object bearing the same
type name; the type alone proves no verification occurred. The demo trusts its
local server and checks response context and checksum consistency. The Markdown
renderer is presentation code, not a second verifier.

## Interfaces and limits

- MCP: `get_investigation_report(case_id, case_version)` is the fourth read-only tool.
- HTTP: `GET /cases/{case_id}/report?case_version=...` uses the same implementation.
- CLI: `python -m reconforge.report_demo [--case-id ...] [--json]` retrieves a report
  through an actual MCP stdio connection.
- Errors: unknown case is HTTP 404, stale version 409, malformed requests or
  report validation/limit failures 422. MCP reports tool errors.
- At most 100 event differences and 256 characters per reported event ID. Larger
  reports fail explicitly; findings are never silently truncated.
- Existing source bounds remain 1 MiB and 1,000 data records per file, at most
  32 configured cases, and exactly one bank payout record per case.

Reports use in-memory captured rows, not a second read of source files. Source
descriptions never become narrative or instructions. Displayed event IDs have
control characters and Markdown syntax escaped. These properties are tested;
LLM prompt-injection resistance is not claimed because no model is involved.

## Consequences and future work

The two fixtures now have reproducible, readable investigation examples and an
explicit contract for downstream consumers. The bank report preserves its
unknown cause; equal net totals do not erase offsetting event discrepancies.

This is bounded demonstration software. There is no authentication, customer
data support, durable audit log, independent source attestation, or financial
action executor. Verification describes consistency with captured inputs, not
their truth or completeness.

A later model-assisted investigator can use these reports as evidence. New
model-authored proposals must have a separate schema, permitted claim/action
types, explicit uncertainty, and adversarial evaluations. Free-form prose must
not inherit the current report's verification status. Human approval and any
future action execution require their own authenticated, version-bound design.
