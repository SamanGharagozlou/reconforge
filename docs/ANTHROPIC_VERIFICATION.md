# Anthropic live-provider verification

Date: 25 September 2026. Implementation: 0.0.6.

## Scope

This increment adds an Anthropic Messages API adapter behind ReconForge's
existing `DecisionModel` boundary. It does not change deterministic financial
calculations, captured evidence identities, fixed investigation reports, MCP
tool authority, or the host-side proposal validator.

The OpenAI adapter remains available. Anthropic support is an additional
provider path rather than a replacement for the existing architecture.

## Offline verification

Local macOS verification used Python 3.12.9.

- `python -m pip check`: no broken requirements.
- Full offline suite: 122 tests passed in 2.765s.
- Bank-shortfall scripted investigator: contract passed.
- Invoice-deduction scripted investigator: contract passed.
- Offline and CI tests require no provider credential or paid API call.

## Live Anthropic acceptance

Provider: Anthropic Messages API.
Requested model: `claude-sonnet-5`.

### Bank-shortfall case

The live run completed successfully with:

- mode `anthropic_live`;
- contract status `passed`;
- priority quality `not_evaluated`;
- 5 provider requests;
- 29,569 reported input tokens;
- 1,048 reported output tokens.

The deterministic report retained:

- ledger total EUR 82,000.00;
- provider total EUR 82,000.00;
- bank total EUR 81,850.00;
- ledger/provider residual EUR 0.00;
- provider/bank residual EUR 150.00;
- cause undetermined and proposed explanations explicitly unverified.

### Invoice-deduction case

The first live submission was rejected by the ReconForge host because the
proposal did not retain the complete applicable playbook. No invalid proposal
was accepted.

The provider-facing submission schema was then tightened so that each ordering
field exposes only the playbook codes applicable to the selected verified
report and explicitly requires every applicable code exactly once. The local
validator remains authoritative and was not weakened.

After that change, the invoice-deduction live run completed successfully with
mode `anthropic_live` and contract status `passed`.

The deterministic case semantics remained unchanged:

- ledger total EUR 115,300.00;
- provider total EUR 115,050.00;
- bank total EUR 115,050.00;
- ledger/provider residual EUR 250.00;
- provider/bank residual EUR 0.00;
- the provider-only `InvoiceDeduction` remains EUR -250.00;
- cause remains undetermined.

Exact token/request counts for the successful invoice run were not retained in
this verification note and are therefore not claimed.

## What this establishes

This establishes that both bundled synthetic cases can complete the bounded
investigator loop through the Anthropic provider adapter while preserving the
existing host contract and deterministic financial facts.

It does not establish model-priority quality, production readiness, source
authenticity, external completeness, tenant authorization, general
prompt-injection resistance, or causal correctness beyond the deterministic
report contract.
