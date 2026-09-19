# ADR 0003: bounded case catalogue and case-scoped evidence

Status: accepted for the local synthetic prototype, 18 September 2026.

## Problem

The first API/MCP store exposes a single case and its list summary contains only
the ledger-to-provider residual. A bank discrepancy could therefore be invisible
to a client that inspects only that number. Supporting another case also creates
a risk that a repeated event ID or shared source bytes return the wrong case's
evidence context.

## Decision

`CaseStore()` captures both bundled fixtures at startup. Operator code can
instead supply `CaseStore(fixtures={case_id: directory, ...})`. The existing
`CaseStore(directory)` call still loads one invoice-ID case for fixture testing.
These configuration paths are never exposed as HTTP or MCP inputs. The catalogue
accepts 1 to 32 valid case IDs, sorts them for stable listing, and validates every
configured case before publishing the store. One invalid case prevents startup.

Each case has its own immutable evidence mapping. Retrieval resolves the case,
checks its version, then looks up the evidence ID inside that mapping. Client
identifiers never become filesystem paths. The existing source-byte, record and
description limits remain applied to each case.

Case versions already include the case ID and source snapshots. Evidence IDs
remain content-derived so the first case's published identifiers stay stable.
Identical source bytes registered under different case IDs may legitimately
share evidence IDs; they still have distinct case versions and response context.
An evidence ID is not globally unique ownership proof or an authorization token.

Each summary now includes `provider_to_bank_residual_minor` as well as
`ledger_to_provider_residual_minor`. Clients must inspect both and the overall
`review_required` flag. The financial engine remains unchanged.

## Compatibility and limits

- The first case's full response schema, calculated facts, version and evidence
  IDs are unchanged. The application version advances to 0.0.3.
- The list response has two cases and an additional summary field. Consumers
  that enforce the previous strict summary schema must update with this release.
- No pagination is needed for the bounded prototype catalogue. Database-backed
  querying, concurrency policies and larger datasets need a separate design.
- Every configured case is readable by local callers. Case separation does not
  implement tenant authorization; no customer data should be added to this demo.
- Only the supplied records are compared. A positive bank residual does not
  establish a cause, missing external transaction, or permission to post money.

## Verification

Tests cover both discrepancy types; the original published identifiers; repeated
event IDs; identical files registered under two case IDs; rejected cross-case
evidence and versions; one-case-only changes after a source edit; invalid startup
configuration; HTTP responses; and both real MCP stdio demonstrations.
