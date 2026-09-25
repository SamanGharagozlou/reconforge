# Day 4 — the first bounded model-assisted investigator

21 September 2026. Local synthetic milestone 0.0.5.

The new investigator reads a case and its verified report through MCP, selects
evidence to inspect, and proposes an ordering of the existing investigation
playbook. The host checks the proposal. Financial facts and report wording remain
deterministic. Live mode uses model function calling; default mode is an explicitly
labelled script for development and CI.

## 1. Apply the update

Start from your clean, synced `main` at version `0.0.4`:

```bash
git status
python3 -c "import reconforge; print(reconforge.__version__)"
```

If necessary, finish the previous PR, switch to `main`, and use VS Code's
**Cmd+Shift+P → Git: Pull**. Save `ReconForge_Bounded_Investigator.patch` in Downloads:

```bash
git switch -c feat/bounded-investigator && \
git apply --check ~/Downloads/ReconForge_Bounded_Investigator.patch && \
git apply ~/Downloads/ReconForge_Bounded_Investigator.patch
```

Stop at any patch error and keep its output. The dependency versions and CI
workflow are unchanged; only the requirements comment is updated.

## 2. Run the offline checks first

```bash
source .venv/bin/activate && \
python -m unittest discover -s tests -v && \
python -m reconforge.investigator_demo --case-id case_bank_shortfall_001 && \
python -m reconforge.investigator_demo
```

Expected: **110 tests pass**. The bank run uses two scripted turns, including one
evidence read and submission. The invoice uses three turns, including the bank
row, missing invoice row, and submission. Both show:

```text
Mode: scripted_offline
Contract checks: passed
Priority quality: not evaluated
Conclusion: cause_undetermined
```

The Markdown output includes formatting around these labels. The bank residual
is EUR 150.00 and the invoice ledger residual is EUR 250.00. No Uvicorn server is
needed: the client starts and closes its own MCP subprocess.

Open `examples/investigator/bank_scripted.md` and use **Cmd+Shift+V** to preview it.
This example is a simulation. It is not evidence that an LLM has completed a run.

## 3. Make the first real model call

You need an OpenAI API key, API quota, and access to a Responses-compatible model.
The example uses a documented snapshot supporting function calling; account
availability must be checked in your own project. This first run is an acceptance
check, not an established model recommendation or quality benchmark.

```bash
python -m reconforge.investigator_demo --case-id case_bank_shortfall_001 --live --model gpt-4.1-mini-2025-04-14
```

If `OPENAI_API_KEY` is not already set, the program asks for it in a hidden terminal
prompt. Paste the key there and press Enter; characters will not appear. The
program does not save it. Do not paste the key into chat, source code, screenshots,
or a Git commit. There is no need to add credentials to GitHub Actions.

Live mode sends the synthetic report, catalogue, and selected evidence fields to
`api.openai.com`. Source descriptions are omitted. The request uses `store: false`;
this setting alone is not a zero-retention guarantee. Check your provider project
settings before considering any future real data. This project currently uses
synthetic fixtures only.

An accepted run will show `openai_live`, the requested model, nonzero provider
request and token counts, and an execution trace. Its exact ordering may differ
from the offline script. It must preserve both residuals, all findings, all
applicable questions/steps, and the undetermined cause. Incomplete responses,
refusals, invalid proposals, and provider errors stop the run. They never fall
back to a fake successful model result.

If the command reports HTTP 401, check the key; for 403, check project/model
permissions; for 429, check API quota or rate limits. Send only the sanitized
error message if you need help. Do not repeatedly rerun a failing paid request.

For a successful machine-readable run, add `--json`. The output contains the
proposal, deterministic report, model identity, reported usage, and tool trace.
It excludes API keys and provider reasoning items. Keep live-run captures in the
ignored `private-data/` directory until you have reviewed them for publication.

## 4. Understand the bounds

| Control | Enforced limit |
| --- | --- |
| Selected case and version | Bound by host; the model cannot change them |
| Model turns | At most 6 |
| Evidence reads | At most 4 distinct rows |
| Findings | At most 12 for this investigator |
| Output tokens | At most 4,096 per API request |
| Request body | At most 96 KiB |
| Response body | At most 256 KiB |
| Provider timeout | 30 seconds per HTTP phase; 10 seconds to connect |
| Whole run | 180 seconds, including local MCP work |
| Automatic retries | None |

These bound execution; they do not set an exact monetary budget. Actual charges
depend on the model, repeated input, and provider-reported usage. The CLI makes
paid requests only when you explicitly use `--live`.

## 5. Review and publish the implementation

Review the diff. Once the offline tests pass:

```bash
git add README.md CONTRIBUTING.md requirements.txt docs examples/investigator reconforge tests && \
git diff --cached --check && \
git commit -m "Add bounded investigator with optional model tool calling"
```

Use **Cmd+Shift+P → Git: Push**. Open `feat/bounded-investigator` → `main` with the
same title. Report actual results separately: offline suite, macOS demonstration,
GitHub Actions, and live API acceptance. If live execution has not succeeded,
keep that status explicit. Inspect the PR diff and passing checks before merge.

## Explain the architecture

The model decides which permitted tool to request. The host validates the
request and supplies the fixed case context. MCP carries the evidence request
to the local server. The host checks the final structured proposal. Only then
does the program render a result for a person.

`contract_status: passed` means the plan obeys those rules. It does not mean its
priority order has been judged useful or its suggested causes have been proved.
This first agent ranks a fixed playbook; it does not invent novel explanations,
execute a resolution, or coordinate multiple agents.

Read `investigation.py` for the contract, `investigator.py` for the loop, and
`openai_model.py` for the provider boundary. The design is recorded in
[ADR 0005](architecture/0005-bounded-investigator.md).

## Official provider references

- [Function calling](https://developers.openai.com/api/docs/guides/function-calling)
- [Structured output constraints](https://developers.openai.com/api/docs/guides/structured-outputs)
- [Reasoning state and stateless requests](https://developers.openai.com/api/docs/guides/reasoning)
- [Example model and snapshot](https://developers.openai.com/api/docs/models/gpt-4.1-mini)
