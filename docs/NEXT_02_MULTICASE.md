# Next increment: multiple cases and a bank discrepancy

18 September 2026. Local synthetic milestone 0.0.3.

The first case detects a provider invoice missing from the supplied ledger.
The second case has matching ledger/provider events but a lower bank payout.
They now share one API and MCP server while retaining separate evidence context.

## Apply the update

Start from the committed 0.0.2 code. If the previous pull request has been merged,
switch to `main` and use VS Code's **Git: Pull** first. Save the new
`ReconForge_Multiple_Cases.patch` in Downloads, then check:

```bash
git status
python3 -c "import reconforge; print(reconforge.__version__)"
```

The working tree should be clean and the version should be `0.0.2`.
From the project root:

```bash
git switch -c feat/multiple-cases && \
git apply --check ~/Downloads/ReconForge_Multiple_Cases.patch && \
git apply ~/Downloads/ReconForge_Multiple_Cases.patch
```

Success is normally silent after the branch message. The `&&` operators stop
the sequence on the first failure. If the check fails, keep the error output;
do not force the patch or reset your work. No dependency or workflow edit is
needed for this increment.

## Run the checks and both demonstrations

Use the environment you already created:

```bash
source .venv/bin/activate && \
python -m unittest discover -s tests -v && \
python -m reconforge.mcp_demo && \
python -m reconforge.mcp_demo --case-id case_bank_shortfall_001
```

Expected: **48 tests pass**. The first demonstration keeps its EUR 250.00 ledger
residual. The second prints:

```text
Case: case_bank_shortfall_001
Ledger-to-provider residual: EUR 0.00
Provider-to-bank residual: EUR 150.00
Evidence: bank_entries.csv, data record 1, evt_bank_001
Evidence amount: EUR 81850.00
```

It also prints the source hash, version, review flag and completeness limit.
The reason for the bank difference is explicitly undetermined. The bank row is
one side of the comparison; the provider components support the other side.

## Inspect both cases through HTTP

```bash
python -m uvicorn reconforge.api:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/docs`. Use **Try it out -> Execute** on `GET /cases`.
It should list both case IDs and both residual fields. The order is sorted by
case ID; clients must select by ID rather than treating the first result as
the invoice case.

For `GET /cases/{case_id}`, use `case_bank_shortfall_001`. Expect:

- `facts.comparisons.ledger_to_provider.residual_minor`: `0`.
- `facts.comparisons.provider_to_bank.residual_minor`: `15000`.
- `facts.event_differences`: `[]`.
- `facts.review_required`: `true`.

From this response, copy `case_version` and the evidence ID whose file is
`bank_entries.csv` into the evidence endpoint. Expect `row.amount_eur` to be
`81850.00`. Keep case IDs, versions and evidence IDs from the same case together.
Stop the server with Ctrl+C when finished.

## Commit and publish

Review the changes in VS Code. After local tests and demos pass:

```bash
git add README.md docs examples/bank_shortfall reconforge tests && \
git diff --cached --check && \
git commit -m "Support multiple cases and a bank payout discrepancy"
```

Use **Cmd+Shift+P -> Git: Push** and publish `feat/multiple-cases` to `origin`.
Open a pull request to `main`. The existing workflow installs the same dependencies
and discovers all 48 tests. Review the diff and wait for the pull-request checks
before merging. Confirm the new macOS and GitHub results in the verification
record when those runs have actually completed.

## What to explain in a portfolio demonstration

The financial core distinguishes a missing ledger event from a bank settlement
difference. An MCP client selects a case, reads exact integer-cent facts, and
retrieves source rows tied to that case's captured version. Matching one pair of
totals does not resolve a discrepancy elsewhere or prove external completeness.

Next: define the investigation output and evaluation criteria before adding an
agent that separates evidenced facts, hypotheses and unresolved questions.
