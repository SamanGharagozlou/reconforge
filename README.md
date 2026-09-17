# ReconForge

 [![Tests](https://github.com/SamanGharagozlou/reconforge/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/SamanGharagozlou/reconforge/actions/workflows/tests.yml). 

Payment reconciliation investigations with traceable evidence.

**Status: preliminary foundation, 17 September 2026.** This starter contains a
deterministic financial example and its tests. MCP servers, agents, authentication,
approval workflows, databases, and a web interface are planned and are not
implemented in this version. ReconForge is a working name.

## Run the first example

Use Python 3.12 or newer from the extracted `reconforge-starter` directory.
No third-party packages, accounts, API keys, or network calls are needed.

```bash
python3 -m reconforge.demo
python3 -m unittest discover -s tests -v
```

The supplied fictional merchant has the following settlement totals:

| Source | EUR |
| --- | ---: |
| Internal ledger | 115,300.00 |
| Payment-provider components | 115,050.00 |
| Bank payout | 115,050.00 |
| Ledger minus provider | **250.00** |
| Provider minus bank | **0.00** |

The provider file includes `evt_invoice_001`, a EUR -250.00 invoice deduction.
The ledger file omits that event. The program reports the difference and source
row so a person can verify it. This is deterministic set comparison on canonical
fixture IDs, not an AI investigation or a real-provider matching integration.

For machine-readable output:

```bash
python3 -m reconforge.demo --json
```

For another directory using the same strict demonstration schema:

```bash
python3 -m reconforge.demo --data-dir examples/invoice_deduction --json
```

## What is implemented

- Exact EUR parsing into integer cents; floats and sub-cent inputs are rejected.
- Strict CSV headers, required fields, timestamp and event-type validation.
- Duplicate event detection and rejection of mixed source scopes.
- Separate ledger-to-provider and provider-to-bank residuals.
- Missing, extra, and changed canonical-event comparisons.
- Source filenames, CSV record references, and SHA-256 source snapshots.
- A rule that offsetting event differences still require review, even if totals balance.
- An offline test suite and a reproducible synthetic fixture.

## What these results mean

`balanced_by_total` only describes the supplied files. It does not prove that
external reporting is complete, that the original records are true, or that an
accounting adjustment should be posted. File hashes identify the bytes read;
they are not proof of trusted provenance. Tenant labels here are data fields,
not authentication or access control.

This example supports one tenant, merchant, payout batch, and currency per run,
with exactly one bank payout entry. It is not production financial software.
Its signed ledger rows are an operational cash projection, not double-entry
general-ledger records. No money moves and no journal entries are posted.

## Direction of the project

The intended product combines a deterministic reconciliation core with three
bounded roles: investigator, resolution planner, and verifier. Those roles will
use scoped MCP tools and prepare evidence-linked proposals for human review.
Permissions, calculations, and approval transitions will remain server-enforced.

The first public milestone is a working synthetic investigation demonstration.
The day-30 target is an evaluated v0.1 with documented limitations. Those are
targets, not released capabilities.

## Start here

- [Tonight's short setup](START_HERE.md)
- [Tomorrow's checklist](docs/DAY_01.md)
- [Scope and acceptance criteria](docs/SCOPE.md)
- [Financial-core design decision](docs/architecture/0001-financial-core.md)
- [Fixture definitions](examples/invoice_deduction/README.md)
- [Contribution instructions](CONTRIBUTING.md)

## License

Apache-2.0; see [LICENSE](LICENSE). All bundled example records are synthetic.
The fixture does not claim compatibility with a production payment-provider
report. No affiliation with payment providers or target employers is implied.
