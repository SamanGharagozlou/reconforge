# Decision 0001 — Deterministic financial core

Date: 17 September 2026.
Status: accepted for the preliminary foundation.

## Context

The product investigates financial differences using agents and source evidence.
Its correctness must not depend on a language model performing arithmetic or
deciding whether it is authorized to act.

## Decision

- Parse the current normalized EUR schema using strict decimal strings.
- Store and calculate amounts as integer cents.
- Compare ledger-to-provider and provider-to-bank independently.
- Preserve filenames, record numbers, and hashes of the exact bytes read.
- Report event-level differences even when net totals balance.
- Return structured findings that future APIs and MCP tools can expose.
- Keep human review and financial actions outside the current baseline.

## Consequences

The example is reproducible without network access or a model key. Future agents
will consume the calculated facts, retrieve additional evidence, and draft a
resolution. They will not replace the core calculations.

The strict initial schema intentionally supports only one batch, one EUR currency,
one merchant and one bank payout. Provider-specific adapters must normalize into
a documented model later; this fixture is not an Adyen-format connector.

## Trust limitations

SHA-256 binds a reference to file bytes; it does not authenticate a provider.
Scope fields detect accidental mixing; they do not implement tenant security.
Equal totals describe supplied records; they do not establish completeness.
Agent, permission, approval, and persistence designs will receive separate decisions.
