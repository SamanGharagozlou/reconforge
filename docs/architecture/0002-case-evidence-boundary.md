# Decision 0002 — one captured case behind two read-only interfaces

Date: 18 September 2026. Status: accepted for the local synthetic prototype.

## Problem

A tool that recalculates from files on every request can show an old discrepancy
with evidence from newly edited files. A tool that accepts arbitrary paths also
exposes far more of the host machine than this workflow needs.

## Decision

Capture the three allow-listed fixture files at startup with byte and record
limits. Use those same bytes for deterministic reconciliation and evidence row
parsing. The new `reconcile_snapshots` entry point shares the existing comparison
function with the original file-based demo; transport code contains no money math.

Return frozen Pydantic models with integer money fields. The case version is the
SHA-256 of canonical case identity, schema version, and facts including source
hashes. Each evidence ID binds filename, source hash, data record number, and
event ID. Evidence requests must include the current case version.

HTTP and MCP use the same store. They accept case and evidence IDs, never paths
or URLs. Requests do not reread disk or perform financial mutations. Host-facing
MCP outputs have typed schemas and read-only annotations. Local HTTP exposes GET
routes and defaults in our documented command to 127.0.0.1.

## Consequences

Evidence is stable for a process lifetime. Restart is necessary to ingest fixture
edits. A case version changes even for a description-only byte change, because
the source hash changes. This is deliberate and does not prove business meaning
changed. It also does not prove the three external systems were captured at the
same instant or that a provider is authoritative.

Unknown case/evidence IDs yield explicit lookup errors. A stale case version
yields HTTP 409 or an MCP tool error. Validation failures yield HTTP 422 or an
MCP tool error. There are no methods for approval, posting, or payment.

The fixture labels and ID checks do not implement authorization. A future
multi-tenant deployment needs principal-bound access, durable snapshots,
auditing, retention policies, and separately reviewed write workflows.
