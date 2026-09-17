# Day 1 checklist

Planned date: 18 September 2026.

## Starting position

The initial synthetic example, strict EUR parser, source references, and tests
are already prepared. Begin by running and understanding them.

## Session 1 — Run and understand

- [ ] Run the demo and test suite from a fresh extraction.
- [ ] Explain the sign convention: captures add; deductions subtract.
- [ ] Explain why ledger-to-provider and provider-to-bank are separate checks.
- [ ] Explain why matching totals alone do not prove matching events.
- [ ] Read `reconforge/money.py`, then the `reconcile` function.

## Session 2 — Prepare the repository

- [ ] Choose the GitHub account and confirm the working repository name.
- [ ] Review the README's implemented/planned distinction.
- [ ] Initialize Git locally and review the files before the first commit.
- [ ] Create and publish the repository when ready; do not include private data.
- [ ] Add a short description and relevant topics after publication.

Suggested description:
“Open-source payment reconciliation investigations with traceable evidence.”

## Session 3 — Define the next small implementation

- [ ] Review the eight cases in `SCOPE.md`.
- [ ] Choose invoice deduction as the first complete user workflow.
- [ ] Define a typed case object from the existing result.
- [ ] Add one documented API endpoint for that case before designing a full UI.
- [ ] Keep the current baseline and tests runnable while adding the next layer.

## Session 4 — Validate the problem

- [ ] Identify three finance or payment-operations practitioners.
- [ ] Ask for a short walkthrough of a recently resolved discrepancy.
- [ ] Record time spent, systems checked, missing evidence, and approval steps.

Done means: the baseline runs, you can explain the calculation and limitations,
the repository is ready to share, and the next issue has clear acceptance criteria.
The first MCP tool will expose existing evidence retrieval after this foundation
is understood; it must not change the arithmetic.
