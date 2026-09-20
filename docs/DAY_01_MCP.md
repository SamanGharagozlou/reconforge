# Day 1 — a typed case, its evidence, and real MCP tools

18 September 2026. This is the 0.0.2 local synthetic milestone.

This walkthrough records that earlier milestone. For the current report
version and 75-test suite, use [the Day 3 walkthrough](DAY_03_REPORTS.md).

## What you should be able to explain

The internal ledger totals EUR 115,300.00. The provider reports EUR 115,050.00
after a EUR -250.00 invoice deduction missing from the supplied ledger extract.
The bank payout matches the provider at EUR 115,050.00. These are two separate
comparisons: the ledger discrepancy requires review even though the payout
balances by total. The comparison cannot prove external reporting completeness.

The core calculates those facts with integer cents. The API and MCP server expose
the same typed case and evidence store. The MCP demo uses a deterministic client
to call the tools; there is no language model or autonomous investigator yet.

## Apply the patch to your existing checkout

Download `ReconForge_Day1_MCP.patch` into your Mac's Downloads folder. In the
existing `reconforge-starter` folder, first save your work and check `git status`.
The previous night's committed changes should be clean. Then:

```bash
git switch -c feat/read-only-mcp
git apply --check ~/Downloads/ReconForge_Day1_MCP.patch
git apply ~/Downloads/ReconForge_Day1_MCP.patch
git diff --stat
```

The check should finish silently. If it reports a conflict, stop and inspect
the error. The patch updates the existing project; it does not create a second
repository. It preserves the README badge. It changes CI to install the pinned
dependencies before running the expanded test suite.

## Install and verify

From the repository root, with Python 3.12 or newer:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip check
python -m unittest discover -s tests -v
python -m reconforge.mcp_demo
```

Expected: 33 tests pass. The final command starts a real MCP subprocess, performs
tool discovery, reads the case and evidence, then shuts the subprocess down.
It should print:

```text
ReconForge 0.0.2 — read-only MCP round trip
Transport: stdio; real MCP client and server
Tools: get_case, get_evidence, list_cases
Case: case_invoice_deduction_001
Ledger-to-provider residual: EUR 250.00
Provider-to-bank residual: EUR 0.00
Evidence: psp_events.csv, data record 7, evt_invoice_001
```

It also prints the source hash, case version, and explicit review/completeness
flags. The bundled provider hash starts with `f50c1ae81978`. No API key or paid
model is required. Dependencies need network access only during installation.

The original command `python -m reconforge.demo` remains available. It performs
the financial calculation directly, without MCP or HTTP.

## Inspect the API

```bash
python -m uvicorn reconforge.api:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/docs` in your browser. Use **Try it out** on
`GET /cases/{case_id}` with `case_invoice_deduction_001`, then **Execute**.
The response should show `facts.comparisons.ledger_to_provider.residual_minor`
equal to `25000` and `facts.review_required` equal to `true`.

To retrieve the missing invoice record, find the item in `evidence` whose
`event_id` is `evt_invoice_001`. Copy its `evidence_id` and the response's
`case_version` into `GET /cases/{case_id}/evidence/{evidence_id}`.
The returned `row.amount_eur` must be `-250.00`. The `record_number` counts CSV
data records excluding the header; it is not a general-purpose physical line number.

Stop the API with Ctrl+C. On a later terminal session, reactivate the environment
with `source .venv/bin/activate` before using the new components.

## Read the implementation in this order

1. `money.py`: why financial values are exact integer cents.
2. `reconciliation.py`: the two residuals and event-level comparisons.
3. `cases.py`: typed facts, snapshot versioning, and evidence IDs.
4. `api.py`: the HTTP interface to the store.
5. `mcp_server.py`: the MCP interface to that same store.
6. `mcp_demo.py`: a real client calls the tools over stdio.

Try explaining why a file edited after server startup must not silently change
the evidence for an already retrieved case. The store retains the captured data
until restart. Restarting against edited files produces a new case version.

## Commit and publish the feature branch

After the tests and demo pass, review changes in VS Code's Source Control panel.
Stage the update there, or use `git add` with the specific changed files shown
by `git status`. Commit with:

```bash
git commit -m "Add typed cases, evidence API and read-only MCP tools"
```

Use **Command Palette → Git: Push**. Publish the feature branch to `origin` when
prompted. GitHub Actions should run all 33 tests. Open a pull request from
`feat/read-only-mcp` to `main`; inspect its diff and successful check before merge.
Your main-branch badge continues to describe `main` until the branch is merged.

## Limits of this milestone

- One synthetic case; no tenant isolation or authenticated users.
- The HTTP demo binds to loopback. Do not deploy this unauthenticated app as a
  customer service. MCP is stdio only in this entry point.
- Snapshot hashes identify bytes, not source authenticity or reporting completeness.
- A case version is not an approval token or a signature.
- Read-only annotations are client hints. The actual tools expose only lookup
  operations; no approval, accounting, payment, path, or URL operation exists.
- Source descriptions are marked as untrusted data. No LLM prompt-injection
  resistance has been claimed or evaluated.
- Each source is capped at 1 MiB and 1,000 data records in the case store. Each
  evidence call returns exactly one captured row. Descriptions are at most 2,048
  characters. This is a bounded demonstration, not a scale benchmark.
- MCP host UI integration on your Mac is a separate check; the stdio client/server
  exchange and HTTP contract are tested here.

## References

- [Official MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [MCP client transports](https://py.sdk.modelcontextprotocol.io/client/transports/)
- [FastAPI testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [VS Code MCP setup](https://code.visualstudio.com/docs/agent-customization/mcp-servers)
