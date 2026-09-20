"""Bounded, deterministic investigation reports verified against captured rows.

Verification accepts this fixed report grammar. It is not a general natural-
language fact checker, a provenance guarantee, or financial authorization.
"""

import json
import re
from datetime import datetime
from hashlib import sha256
from typing import Annotated, Literal

from pydantic import Field, StrictBool, StrictInt, StrictStr, ValidationError, model_validator

from .cases import (
    CaseId, CaseStore, CaseVersionMismatch, Difference, Digest, EvidenceRecord,
    EvidenceReference, FrozenModel, ReconciliationCase, SourceReference, SourceSnapshot,
)
from .money import format_eur, parse_eur
from .reconciliation import SOURCE_FILES

MAX_EVENT_FINDINGS = 100
Text = Annotated[StrictStr, Field(min_length=1, max_length=1000)]
FindingId = Annotated[StrictStr, Field(pattern=r"^f_[0-9]{3}$")]


class SnapshotCitation(FrozenModel):
    kind: Literal["snapshot"] = "snapshot"
    source: SourceSnapshot


class RowCitation(FrozenModel):
    kind: Literal["row"] = "row"
    reference: EvidenceReference


Citation = Annotated[SnapshotCitation | RowCitation, Field(discriminator="kind")]


class Finding(FrozenModel):
    finding_id: FindingId
    kind: Literal[
        "ledger_total", "provider_total", "bank_total", "ledger_to_provider", "provider_to_bank",
        "provider_event_absent_from_ledger", "ledger_event_absent_from_provider", "event_values_differ",
    ]
    statement: Text
    amount_minor: StrictInt | None
    event_id: Annotated[StrictStr, Field(min_length=1, max_length=256)] | None = None
    citations: Annotated[tuple[Citation, ...], Field(min_length=1, max_length=3)]


class Hypothesis(FrozenModel):
    code: Literal["ledger_import_or_recording", "payout_timing_or_reporting", "adjustment_or_data_error"]
    status: Literal["unverified"] = "unverified"
    statement: Text
    trigger_finding_ids: Annotated[tuple[FindingId, ...], Field(min_length=1, max_length=2)]


class UnresolvedQuestion(FrozenModel):
    code: Literal["external_completeness", "ledger_difference_cause", "bank_difference_cause"]
    question: Text


class NextStep(FrozenModel):
    code: Literal["obtain_complete_reports", "inspect_ledger_records", "compare_payout_advice"]
    kind: Literal["information_request"] = "information_request"
    owner: Literal["human_analyst"] = "human_analyst"
    instruction: Text


class InvestigationReport(FrozenModel):
    schema_version: Literal["0.1.0"] = "0.1.0"
    policy_version: Literal["0.1.0"] = "0.1.0"
    generator: Literal["deterministic_rules"] = "deterministic_rules"
    case_id: CaseId
    case_version: Digest
    currency: Literal["EUR"] = "EUR"
    findings: Annotated[tuple[Finding, ...], Field(min_length=5, max_length=5 + MAX_EVENT_FINDINGS)]
    hypotheses: Annotated[tuple[Hypothesis, ...], Field(max_length=3)]
    unresolved_questions: Annotated[tuple[UnresolvedQuestion, ...], Field(min_length=1, max_length=3)]
    next_steps: Annotated[tuple[NextStep, ...], Field(min_length=1, max_length=3)]
    review_required: StrictBool
    external_completeness_verified: StrictBool = False
    financial_actions_allowed: StrictBool = False

    @model_validator(mode="after")
    def preserve_limits(self):
        if self.external_completeness_verified or self.financial_actions_allowed:
            raise ValueError("Reports cannot certify completeness or authorize financial actions.")
        return self


class ReportVerification(FrozenModel):
    status: Literal["passed"] = "passed"
    scope: Literal["captured_rows_and_fixed_report_rules"] = "captured_rows_and_fixed_report_rules"
    findings_checked: StrictInt
    citations_checked: StrictInt


class VerifiedReport(FrozenModel):
    report_id: Digest
    report: InvestigationReport
    verification: ReportVerification


class ReportValidationError(ValueError):
    """The report or its claimed financial facts do not match the captured case."""


class ReportLimitError(ValueError):
    """The captured case is larger than this bounded report format supports."""


def draft_report(case: ReconciliationCase) -> InvestigationReport:
    """Build a draft using fixed statements; source descriptions are never prose."""
    differences = case.facts.event_differences
    if len(differences) > MAX_EVENT_FINDINGS or any(len(d.event_id) > 256 for d in differences):
        raise ReportLimitError("Report limit exceeded: at most 100 event differences and 256-character event IDs.")
    snapshots = {s.file: SnapshotCitation(source=s) for s in case.facts.source_snapshots}
    rows = {(r.file, r.record_number): r for r in case.evidence}
    bank_rows = [RowCitation(reference=r) for r in case.evidence if r.file == "bank_entries.csv"]
    findings = []

    def add(kind, statement, amount, citations, event_id=None):
        findings.append(Finding(
            finding_id=f"f_{len(findings) + 1:03d}", kind=kind, statement=statement,
            amount_minor=amount, event_id=event_id, citations=tuple(citations),
        ))

    for source, file in zip(("ledger", "provider", "bank"), SOURCE_FILES):
        amount = getattr(case.facts.totals_minor, source)
        citations = [snapshots[file]] + (bank_rows if source == "bank" else [])
        add(f"{source}_total", f"Supplied {source} records total {format_eur(amount)}.", amount, citations)
    for kind, label, files in (
        ("ledger_to_provider", "Ledger minus provider", SOURCE_FILES[:2]),
        ("provider_to_bank", "Provider minus bank", SOURCE_FILES[1:]),
    ):
        comparison = getattr(case.facts.comparisons, kind)
        citations = [snapshots[file] for file in files] + (bank_rows if kind == "provider_to_bank" else [])
        add(kind, f"{label}: {format_eur(comparison.residual_minor)}; status: {comparison.status}.",
            comparison.residual_minor, citations)
    for difference in differences:
        citations = []
        for source, file in ((difference.ledger_source, "ledger_events.csv"),
                             (difference.provider_source, "psp_events.csv")):
            citations.append(
                RowCitation(reference=rows[(file, source.record_number)]) if source else snapshots[file]
            )
        if difference.kind == "provider_event_absent_from_ledger":
            amount = difference.provider_amount_minor
            statement = f"A provider event of {format_eur(amount)} is absent from the supplied ledger extract."
        elif difference.kind == "ledger_event_absent_from_provider":
            amount = difference.ledger_amount_minor
            statement = f"A ledger event of {format_eur(amount)} is absent from the supplied provider extract."
        else:
            amount = None
            statement = "A shared event differs in amount, event type, or effective timestamp between the supplied sources."
        add(difference.kind, statement, amount, citations, difference.event_id)

    hypotheses, questions, steps = [], [UnresolvedQuestion(
        code="external_completeness", question="Are the supplied ledger, provider, and bank extracts complete for this batch?",
    )], [NextStep(
        code="obtain_complete_reports",
        instruction="Obtain or confirm the complete source reports and reporting cutoffs for this batch.",
    )]
    if case.facts.comparisons.ledger_to_provider.status == "needs_review":
        hypotheses.append(Hypothesis(
            code="ledger_import_or_recording", trigger_finding_ids=("f_004",),
            statement="An import, extraction, or recording difference could explain the ledger/provider mismatch; its cause is unverified.",
        ))
        questions.append(UnresolvedQuestion(code="ledger_difference_cause", question="Why do the supplied ledger and provider events differ?"))
        steps.append(NextStep(code="inspect_ledger_records", instruction="Inspect the original ledger records and import history for the cited event differences."))
    if case.facts.comparisons.provider_to_bank.residual_minor:
        hypotheses.extend((
            Hypothesis(code="payout_timing_or_reporting", trigger_finding_ids=("f_005",),
                       statement="Different reporting cutoffs or incomplete payout reporting could explain the bank difference; this is unverified."),
            Hypothesis(code="adjustment_or_data_error", trigger_finding_ids=("f_005",),
                       statement="An unreported adjustment or an error in a supplied source could explain the bank difference; this is unverified."),
        ))
        questions.append(UnresolvedQuestion(code="bank_difference_cause", question="What explains the provider-to-bank difference? The supplied records do not establish its cause."))
        steps.append(NextStep(code="compare_payout_advice", instruction="Compare the provider payout advice and complete bank statement, including dates and any separately reported deductions."))
    return InvestigationReport(
        case_id=case.case_id, case_version=case.case_version, findings=tuple(findings),
        hypotheses=tuple(hypotheses), unresolved_questions=tuple(questions), next_steps=tuple(steps),
        review_required=case.facts.review_required,
    )


def _ground_case(store: CaseStore, case: ReconciliationCase) -> dict[str, EvidenceRecord]:
    """Independently recheck case arithmetic and event differences from source rows."""
    records = {}
    groups = {file: {} for file in SOURCE_FILES}
    snapshots = {s.file: s for s in case.facts.source_snapshots}
    if set(snapshots) != set(SOURCE_FILES) or len(case.facts.source_snapshots) != 3:
        raise ReportValidationError("The case must have exactly three source snapshots.")
    for reference in case.evidence:
        record = store.get_evidence(case.case_id, case.case_version, reference.evidence_id)
        if record.reference != reference or record.case_id != case.case_id or record.case_version != case.case_version:
            raise ReportValidationError("Captured evidence context does not match the case.")
        if reference.evidence_id in records or record.row.event_id in groups[reference.file]:
            raise ReportValidationError("Duplicate captured evidence or event ID.")
        if reference.sha256 != snapshots[reference.file].sha256:
            raise ReportValidationError("Evidence hash does not match its captured snapshot.")
        if reference.event_id != record.row.event_id:
            raise ReportValidationError("Evidence event ID does not match the captured row.")
        if any(getattr(record.row, field) != value for field, value in case.facts.scope.model_dump().items()):
            raise ReportValidationError("Evidence scope does not match the case.")
        records[reference.evidence_id] = record
        groups[reference.file][record.row.event_id] = record
    for file, rows in groups.items():
        if {r.reference.record_number for r in rows.values()} != set(range(1, snapshots[file].data_records + 1)):
            raise ReportValidationError("The captured evidence does not cover its source snapshot.")
    if len(groups["bank_entries.csv"]) != 1:
        raise ReportValidationError("Exactly one captured bank payout is required.")

    totals = {source: sum(parse_eur(r.row.amount_eur) for r in groups[file].values())
              for source, file in zip(("ledger", "provider", "bank"), SOURCE_FILES)}
    if totals != case.facts.totals_minor.model_dump():
        raise ReportValidationError("Case totals do not match the captured source amounts.")
    ledger, provider = groups["ledger_events.csv"], groups["psp_events.csv"]
    differences = []

    def values(record):
        row = record.row
        timestamp = datetime.fromisoformat(row.effective_at.replace("Z", "+00:00")).isoformat()
        return parse_eur(row.amount_eur), row.event_type, timestamp

    def source(record):
        return SourceReference.model_validate(record.reference.model_dump(exclude={"evidence_id"})) if record else None

    for event_id in sorted(ledger.keys() | provider.keys()):
        left, right = ledger.get(event_id), provider.get(event_id)
        if left is None:
            kind = "provider_event_absent_from_ledger"
        elif right is None:
            kind = "ledger_event_absent_from_provider"
        elif values(left) != values(right):
            kind = "event_values_differ"
        else:
            continue
        differences.append(Difference(
            kind=kind, event_id=event_id,
            ledger_amount_minor=parse_eur(left.row.amount_eur) if left else None,
            provider_amount_minor=parse_eur(right.row.amount_eur) if right else None,
            ledger_source=source(left), provider_source=source(right),
        ))
    if tuple(differences) != case.facts.event_differences:
        raise ReportValidationError("Case event differences do not match the captured rows.")
    ledger_residual = totals["ledger"] - totals["provider"]
    bank_residual = totals["provider"] - totals["bank"]
    comparisons = case.facts.comparisons
    if (
        comparisons.ledger_to_provider.residual_minor != ledger_residual
        or comparisons.provider_to_bank.residual_minor != bank_residual
        or comparisons.ledger_to_provider.status != ("needs_review" if ledger_residual or differences else "balanced_on_supplied_events")
        or comparisons.provider_to_bank.status != ("needs_review" if bank_residual else "balanced_by_total")
        or case.facts.review_required != bool(ledger_residual or bank_residual or differences)
    ):
        raise ReportValidationError("Case comparisons or review status do not match the captured rows.")
    return records


def verify_report(
    candidate: InvestigationReport | dict, store: CaseStore, *, case_id: str, case_version: str,
) -> VerifiedReport:
    """Verify against caller-selected context; never trust context from the report alone."""
    case = store.get_case(case_id)
    if case.case_version != case_version:
        raise CaseVersionMismatch("Case version changed; retrieve the case again.")
    try:
        data = candidate.model_dump() if isinstance(candidate, InvestigationReport) else candidate
        report = InvestigationReport.model_validate(data)
    except ValidationError as exc:
        raise ReportValidationError("Report does not satisfy the strict report schema.") from exc
    if report.case_id != case_id or report.case_version != case_version:
        raise ReportValidationError("Report belongs to a different case or snapshot version.")
    records = _ground_case(store, case)
    snapshots = {s.file: s for s in case.facts.source_snapshots}
    citation_count = 0
    for finding in report.findings:
        for citation in finding.citations:
            citation_count += 1
            if isinstance(citation, SnapshotCitation):
                if snapshots.get(citation.source.file) != citation.source:
                    raise ReportValidationError("Snapshot citation does not match the captured source.")
            else:
                record = records.get(citation.reference.evidence_id)
                if record is None or record.reference != citation.reference:
                    raise ReportValidationError("Row citation does not belong to this captured case.")
    # Fixed grammar: all findings, supporting sources, uncertainty labels and
    # human information requests must match the allowed rules. This also rejects
    # omissions and citations that exist but do not support the particular claim.
    if report != draft_report(case):
        raise ReportValidationError("Report claims, coverage or uncertainty labels do not match the allowed case rules.")
    canonical = json.dumps(report.model_dump(mode="json"), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return VerifiedReport(
        report_id=sha256(canonical.encode("utf-8")).hexdigest(), report=report,
        verification=ReportVerification(findings_checked=len(report.findings), citations_checked=citation_count),
    )


def get_investigation_report(store: CaseStore, case_id: str, case_version: str) -> VerifiedReport:
    case = store.get_case(case_id)
    if case.case_version != case_version:
        raise CaseVersionMismatch("Case version changed; retrieve the case again.")
    return verify_report(draft_report(case), store, case_id=case_id, case_version=case_version)


def render_markdown(verified: VerifiedReport) -> str:
    """Render an envelope from the trusted verifier/server; not a provenance check."""
    report = verified.report
    lines = [
        "# ReconForge investigation report", "", f"Case: `{report.case_id}`", "",
        "Prepared by deterministic rules. No model calls were used.",
        f"Review required: **{str(report.review_required).lower()}**.",
        "Verification: passed against captured rows and fixed report rules.", "", "## Evidenced facts", "",
    ]
    citations = []
    for finding in report.findings:
        labels = []
        for citation in finding.citations:
            if citation not in citations:
                citations.append(citation)
            labels.append(f"[C{citations.index(citation) + 1}]")
        lines.append(f"- **{finding.finding_id}**: {finding.statement} {' '.join(labels)}")
        if finding.event_id is not None:
            # Escape controls and Markdown syntax in the only free-form source
            # identifier included in the narrative. Descriptions are omitted.
            identifier = re.sub(r"([\\`*_{}\[\]()#+.!|<>-])", r"\\\1", json.dumps(finding.event_id, ensure_ascii=True))
            lines.append(f"  Event ID: {identifier}")
    lines.extend(("", "## Possible explanations — unverified", ""))
    lines.extend(f"- {h.statement}" for h in report.hypotheses)
    if not report.hypotheses:
        lines.append("No discrepancy hypothesis is generated for these supplied records.")
    lines.extend(("", "## Unresolved questions", ""))
    lines.extend(f"- {q.question}" for q in report.unresolved_questions)
    lines.extend(("", "## Next steps for a human analyst", ""))
    lines.extend(f"{i}. {step.instruction}" for i, step in enumerate(report.next_steps, 1))
    lines.extend(("", "## Evidence references", ""))
    for i, citation in enumerate(citations, 1):
        if isinstance(citation, SnapshotCitation):
            ref = citation.source
            unit = "record" if ref.data_records == 1 else "records"
            lines.append(f"- **C{i}**: `{ref.file}`, captured snapshot of {ref.data_records} data {unit}.")
        else:
            ref = citation.reference
            lines.append(f"- **C{i}**: `{ref.file}`, data record {ref.record_number}; evidence `{ref.evidence_id}`.")
        lines.append(f"  SHA-256: `{ref.sha256}`")
    lines.extend((
        "", f"Case version: `{report.case_version}`", "", f"Report ID: `{verified.report_id}`", "",
        "Synthetic data only. External completeness is unverified. Hashes identify captured bytes; "
        "they do not establish trusted provenance. This report authorizes no financial action.", "",
    ))
    return "\n".join(lines)
