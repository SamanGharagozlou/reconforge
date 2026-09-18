# Contributing

This is an early foundation. Discuss larger changes before adding frameworks or
integrations. The current priority is a clear, correct financial example.

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
```

For a change, describe the problem, expected behaviour, relevant source semantics,
and how you verified it. Financial edge cases should include synthetic examples.
Keep real customer records, credentials and proprietary material out of changes.
Case and transport changes should preserve exact money fields, snapshot-bound
evidence, and explicit errors for stale versions. See `docs/DAY_01_MCP.md`.

Useful first contributions include a parser edge case, clearer fixture documentation,
or a proposed scenario with explicit expected totals and review behaviour.

See `LICENSE` for the Apache-2.0 terms.
