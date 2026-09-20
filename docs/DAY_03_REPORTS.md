# Day 3 — evidence-verified investigation reports

20 September 2026. Local synthetic milestone 0.0.4.

Today's outcome: turn either synthetic case into an inspectable investigation
report through a fourth MCP tool. The report contains cited facts, unverified
possibilities, unresolved questions, and requests for a human analyst to obtain
more information. A verifier recomputes the supplied financial facts and rejects
reports that do not match the fixed claim rules.

This increment uses deterministic rules. Model-assisted investigation is a later
increment; this establishes the report contract and its rejection behaviour first.

## 1. Start from the completed multiple-case milestone

Finish the previous `feat/multiple-cases` pull request if needed: review its diff,
wait for successful checks, and merge it into `main`. In the existing VS Code
project, save your files and check `git status`. With a clean working tree:

```bash
git switch main
```

Use **Cmd+Shift+P → Git: Pull**, then run:

```bash
git status
python3 -c "import reconforge; print(reconforge.__version__)"
```

Expected: `main`, a clean working tree, and `0.0.3`. If those differ, inspect the
output before applying the update. No reset or forced overwrite is needed.

## 2. Apply the prepared update

Save `ReconForge_Investigation_Reports.patch` in your Mac's Downloads folder.
From the existing `reconforge-starter` directory:

```bash
git switch -c feat/investigation-reports && \
git apply --check ~/Downloads/ReconForge_Investigation_Reports.patch && \
git apply ~/Downloads/ReconForge_Investigation_Reports.patch
```

After the branch message, success is normally silent. The `&&` operators stop
at the first failed command. If a command fails, keep its exact output and stop
there. The patch uses your existing dependencies and GitHub Actions workflow.

## 3. Run the tests and read the bank investigation

Reuse the environment you already installed:

```bash
source .venv/bin/activate && \
python -m unittest discover -s tests -v && \
python -m reconforge.report_demo --case-id case_bank_shortfall_001
```

Expected: **75 tests pass**, followed by a Markdown report. The report client
starts and closes its own local MCP server; you do not need to start Uvicorn.

Check the five findings:

| Finding | Expected result |
| --- | --- |
| Ledger total | EUR 82,000.00 |
| Provider total | EUR 82,000.00 |
| Bank total | EUR 81,850.00 |
| Ledger minus provider | EUR 0.00; balanced on supplied events |
| Provider minus bank | EUR 150.00; review required |

The report must leave the bank discrepancy's cause unresolved. Reporting cutoffs,
an unreported adjustment, and source errors are possibilities only. The human
next step is to compare payout advice and complete bank records.

For the invoice case and a machine-readable bank report:

```bash
python -m reconforge.report_demo
python -m reconforge.report_demo --case-id case_bank_shortfall_001 --json
```

The invoice report includes an additional finding: a EUR -250.00 provider event
is absent from the supplied ledger extract. That finding cites the provider row
and the captured ledger snapshot. It does not establish why the event is absent.

Open `examples/reports/bank_shortfall.md` in VS Code and press **Cmd+Shift+V** to
preview the readable example. These checked-in reports let GitHub visitors
inspect the outcome before installing the project.

## 4. Inspect the report API

```bash
python -m uvicorn reconforge.api:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/docs`:

1. Execute `GET /cases/{case_id}` with `case_bank_shortfall_001`.
2. Copy its `case_version`.
3. Execute `GET /cases/{case_id}/report` with that case ID and version.
4. Inspect `verification.status`, `report.findings`, `report.hypotheses`, and
   `report.unresolved_questions`.

The response should show verification `passed`, five findings, two hypotheses
labelled `unverified`, `review_required: true`, and both
`external_completeness_verified` and `financial_actions_allowed` set to `false`.
A stale version is rejected with HTTP 409. Stop the server with **Ctrl+C**.

## 5. Review, commit, and publish the branch

Inspect the diff in VS Code's Source Control panel. Then:

```bash
git add README.md CONTRIBUTING.md docs examples/reports reconforge tests && \
git diff --cached --check && \
git commit -m "Add evidence-verified investigation reports"
```

Use **Cmd+Shift+P → Git: Push** and publish `feat/investigation-reports` when
prompted. Open a pull request to `main` with the same title as the commit. Explain
that analysts can now retrieve a cited report, that causes remain unverified,
and that the verifier checks captured facts and fixed rules. Include your actual
test and demo results. Wait for the PR's checks and inspect the diff before merge.

The existing workflow discovers the new tests automatically. The README's
main-branch badge will reflect the change after it reaches `main` and runs there.

## Explain what you built

- Why does the missing-event finding cite both a row and a whole snapshot?
- Why can the bank difference be verified while its cause remains unknown?
- Why is a report digest neither a signature nor an approval?
- Why does checking this fixed grammar not validate arbitrary model-generated prose?

Read `reconforge/reports.py`, then
[`0004-investigation-reports.md`](architecture/0004-investigation-reports.md).
The next model-assisted increment can consume these tools and cite their output.
Allowing model-authored claims will need a separate bounded proposal contract
and evaluations; the current verifier deliberately accepts only its fixed rules.
