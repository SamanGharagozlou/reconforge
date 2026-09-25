"""A bounded model proposal, kept separate from the deterministic report.

Models choose evidence reads and order an existing investigation playbook.
They cannot add free-form factual claims, established causes, or financial actions.
Passing this contract does not establish that a model's priorities are useful.
"""

import json
from hashlib import sha256
from typing import Annotated, Literal

from pydantic import Field, StrictInt, ValidationError

from .cases import CaseId, Digest, EvidenceId, EvidenceRecord, FrozenModel, ReconciliationCase
from .reports import FindingId, RowCitation, VerifiedReport

MAX_EVIDENCE_READS = 4
MAX_FINDINGS = 12
MAX_MODEL_TURNS = 6


class InvestigationError(ValueError):
    """A run stopped without producing an accepted investigation plan."""


class FindingSelection(FrozenModel):
    finding_id: FindingId
    amount_minor: StrictInt | None


class InvestigationProposal(FrozenModel):
    case_id: CaseId
    case_version: Digest
    report_id: Digest
    findings: Annotated[tuple[FindingSelection, ...], Field(min_length=5, max_length=MAX_FINDINGS)]
    evidence_ids: Annotated[tuple[EvidenceId, ...], Field(min_length=1, max_length=MAX_EVIDENCE_READS)]
    hypothesis_order: Annotated[tuple[Literal[
        "ledger_import_or_recording", "payout_timing_or_reporting", "adjustment_or_data_error",
    ], ...], Field(max_length=3)]
    question_order: Annotated[tuple[Literal[
        "external_completeness", "ledger_difference_cause", "bank_difference_cause",
    ], ...], Field(min_length=1, max_length=3)]
    next_step_order: Annotated[tuple[Literal[
        "obtain_complete_reports", "inspect_ledger_records", "compare_payout_advice",
    ], ...], Field(min_length=1, max_length=3)]
    conclusion: Literal["cause_undetermined", "no_discrepancy_in_supplied_records"]


class EvidenceRequest(FrozenModel):
    evidence_id: EvidenceId


class DecisionTrace(FrozenModel):
    turn: StrictInt
    tool: Literal["get_evidence", "submit_investigation"]
    evidence_id: EvidenceId | None


class InvestigationRun(FrozenModel):
    schema_version: Literal["0.1.0"] = "0.1.0"
    mode: Literal["scripted_offline", "openai_live"]
    requested_model: str | None
    returned_models: tuple[str, ...]
    proposal: InvestigationProposal
    report: VerifiedReport
    contract_status: Literal["passed"] = "passed"
    priority_quality: Literal["not_evaluated"] = "not_evaluated"
    financial_actions_allowed: Literal[False] = False
    model_turns: StrictInt
    provider_requests: StrictInt
    input_tokens: StrictInt | None
    output_tokens: StrictInt | None
    trace: tuple[DecisionTrace, ...]


def canonical_json(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def validate_context(case: ReconciliationCase, report: VerifiedReport) -> None:
    """Check a response from the trusted local server; a digest is not a signature."""
    inner = report.report
    if (inner.case_id, inner.case_version) != (case.case_id, case.case_version):
        raise InvestigationError("The report does not match the selected case snapshot.")
    digest = sha256(canonical_json(inner.model_dump(mode="json")).encode()).hexdigest()
    if digest != report.report_id:
        raise InvestigationError("The report content does not match its identifier.")
    if len(inner.findings) > MAX_FINDINGS or len(required_evidence(report)) > MAX_EVIDENCE_READS:
        raise InvestigationError("This investigator supports at most 12 findings and 4 required evidence rows.")
    catalogue = {ref.evidence_id: ref for ref in case.evidence}
    for finding in inner.findings:
        for citation in finding.citations:
            if isinstance(citation, RowCitation) and catalogue.get(citation.reference.evidence_id) != citation.reference:
                raise InvestigationError("A report citation does not match the selected case catalogue.")


def required_evidence(report: VerifiedReport) -> set[str]:
    return {
        citation.reference.evidence_id
        for finding in report.report.findings for citation in finding.citations
        if isinstance(citation, RowCitation)
    }


def validate_record(case: ReconciliationCase, evidence_id: str, record: EvidenceRecord) -> None:
    expected = next((r for r in case.evidence if r.evidence_id == evidence_id), None)
    if (
        expected is None or record.reference != expected
        or (record.case_id, record.case_version) != (case.case_id, case.case_version)
        or record.row.event_id != expected.event_id
        or any(getattr(record.row, key) != value for key, value in case.facts.scope.model_dump().items())
    ):
        raise InvestigationError("The evidence response does not match the requested case and row.")


def validate_proposal(candidate: dict, case: ReconciliationCase, report: VerifiedReport,
                      inspected: dict[str, EvidenceRecord]) -> InvestigationProposal:
    validate_context(case, report)
    try:
        proposal = InvestigationProposal.model_validate(candidate)
    except ValidationError as exc:
        raise InvestigationError("The proposal does not satisfy the bounded investigation schema.") from exc
    if (proposal.case_id, proposal.case_version, proposal.report_id) != (
        case.case_id, case.case_version, report.report_id,
    ):
        raise InvestigationError("The proposal uses a different case, version, or report.")
    expected = {f.finding_id: f.amount_minor for f in report.report.findings}
    actual = {f.finding_id: f.amount_minor for f in proposal.findings}
    if len(actual) != len(proposal.findings) or actual != expected:
        raise InvestigationError("The proposal must preserve every verified finding and exact amount.")
    citations = set(proposal.evidence_ids)
    if len(citations) != len(proposal.evidence_ids) or not citations <= inspected.keys():
        raise InvestigationError("The proposal cites duplicate or unread evidence.")
    if not required_evidence(report) <= citations:
        raise InvestigationError("The proposal must cite every row used by the report's findings.")
    for evidence_id in citations:
        validate_record(case, evidence_id, inspected[evidence_id])
    for order, options in (
        (proposal.hypothesis_order, report.report.hypotheses),
        (proposal.question_order, report.report.unresolved_questions),
        (proposal.next_step_order, report.report.next_steps),
    ):
        if len(set(order)) != len(order) or set(order) != {item.code for item in options}:
            raise InvestigationError("The proposal must retain the complete applicable playbook without additions.")
    conclusion = "cause_undetermined" if report.report.review_required else "no_discrepancy_in_supplied_records"
    if proposal.conclusion != conclusion:
        raise InvestigationError("The conclusion does not preserve the case's uncertainty.")
    return proposal


def proposal_template(case: ReconciliationCase, report: VerifiedReport) -> dict:
    """A deterministic fixture for offline runs/tests, not a model-generated result."""
    return InvestigationProposal(
        case_id=case.case_id, case_version=case.case_version, report_id=report.report_id,
        findings=tuple(FindingSelection(finding_id=f.finding_id, amount_minor=f.amount_minor)
                       for f in report.report.findings),
        evidence_ids=tuple(sorted(required_evidence(report))),
        hypothesis_order=tuple(h.code for h in report.report.hypotheses),
        question_order=tuple(q.code for q in report.report.unresolved_questions),
        next_step_order=tuple(s.code for s in report.report.next_steps),
        conclusion="cause_undetermined" if report.report.review_required else "no_discrepancy_in_supplied_records",
    ).model_dump(mode="json")


def render_investigation(run: InvestigationRun) -> str:
    report, proposal = run.report.report, run.proposal
    lines = ["# ReconForge investigator", "", f"Case: `{proposal.case_id}`", "",
             f"Mode: **{run.mode}**."]
    if run.mode == "scripted_offline":
        lines.append("Scripted simulation with real MCP calls. No language model or paid API was used.")
    else:
        lines.append(f"Model requested: {json.dumps(run.requested_model, ensure_ascii=True)}.")
        lines.append(f"Provider requests: {run.provider_requests}; reported input/output tokens: {run.input_tokens}/{run.output_tokens}.")
    lines.extend(("", "Contract checks: **passed**. Priority quality: **not evaluated**.",
                  "Financial facts and wording below come from deterministic rules.",
                  "The investigator chooses evidence reads and the order of follow-up items.",
                  "", "## Verified financial findings", ""))
    lines.extend(f"- {f.finding_id}: {f.statement}" for f in report.findings)
    for title, order, items, field in (
        ("Possible explanations — all unverified", proposal.hypothesis_order, report.hypotheses, "statement"),
        ("Questions in proposed order", proposal.question_order, report.unresolved_questions, "question"),
        ("Human next steps in proposed order", proposal.next_step_order, report.next_steps, "instruction"),
    ):
        lines.extend(("", f"## {title}", ""))
        by_code = {item.code: item for item in items}
        lines.extend(f"{i}. {getattr(by_code[code], field)}" for i, code in enumerate(order, 1))
        if not order:
            lines.append("None for the supplied records.")
    lines.extend(("", "## Execution trace", ""))
    for step in run.trace:
        lines.append(f"- Turn {step.turn}: `{step.tool}`" + (f" — `{step.evidence_id}`" if step.evidence_id else ""))
    lines.extend(("", f"Conclusion: `{proposal.conclusion}`.",
                  "External completeness remains unverified. No financial action is authorized.",
                  "", f"Case version: `{proposal.case_version}`", "", f"Report ID: `{proposal.report_id}`", ""))
    return "\n".join(lines)
