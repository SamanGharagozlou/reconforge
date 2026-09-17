# Contributing

This is an early foundation. Discuss larger changes before adding frameworks or
integrations. The current priority is a clear, correct financial example.

Run the offline checks:

```bash
python3 -m unittest discover -s tests -v
python3 -m reconforge.demo --json
```

For a change, describe the problem, expected behaviour, relevant source semantics,
and how you verified it. Financial edge cases should include synthetic examples.
Keep real customer records, credentials and proprietary material out of changes.

Useful first contributions include a parser edge case, clearer fixture documentation,
or a proposed scenario with explicit expected totals and review behaviour.

See `LICENSE` for the Apache-2.0 terms.
