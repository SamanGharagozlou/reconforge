# Contributing

This is an early foundation. Discuss larger changes before adding frameworks or
integrations. The current priority is a correct, inspectable investigation on
synthetic source records.

From the repository root, set up the pinned environment once:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Then run the checks (the test data and MCP subprocess are local):

```bash
python -m unittest discover -s tests -v
python -m reconforge.demo --json
python -m reconforge.mcp_demo
python -m reconforge.report_demo --case-id case_bank_shortfall_001
```

For a change, describe the problem, expected behaviour, relevant source semantics,
and how you verified it. Financial edge cases should include synthetic examples.
Keep real customer records, credentials and proprietary material out of changes.
Case and transport changes should preserve exact money fields, snapshot-bound
evidence, and explicit errors for stale versions. Report changes must keep facts,
unverified possibilities, and human information requests distinct. Define the
claim rule and supporting source records, then test a plausible invalid report
as well as the expected result. Do not expand the verifier's stated scope to
arbitrary natural-language claims. See
[the report design](docs/architecture/0004-investigation-reports.md).

When report output changes, regenerate the two checked-in examples:

```bash
python -m reconforge.report_demo > examples/reports/invoice_deduction.md
python -m reconforge.report_demo --case-id case_bank_shortfall_001 > examples/reports/bank_shortfall.md
```

Inspect the diff. Update schema or policy versions when their contracts change;
the report digest includes those versions and the complete structured report.

Useful first contributions include a parser edge case, clearer fixture documentation,
or a proposed scenario with explicit expected totals and review behaviour.

See `LICENSE` for the Apache-2.0 terms.
