"""Typed, immutable views of one synthetic case and its captured source rows."""

import csv
import json
from hashlib import sha256
from io import StringIO
from pathlib import Path
from types import MappingProxyType
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt, StrictStr

from .reconciliation import InputError, SOURCE_FILES, reconcile_snapshots

CASE_ID = "case_invoice_deduction_001"
FIXTURE = Path(__file__).resolve().parents[1] / "examples" / "invoice_deduction"
MAX_SOURCE_BYTES = 1_048_576
MAX_SOURCE_RECORDS = 1000

CaseId = Annotated[StrictStr, Field(min_length=1, max_length=80, pattern=r"^[a-zA-Z0-9_-]+$")]
Digest = Annotated[StrictStr, Field(min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$")]
EvidenceId = Annotated[StrictStr, Field(min_length=67, max_length=67, pattern=r"^ev_[0-9a-f]{64}$")]
RecordNumber = Annotated[StrictInt, Field(ge=1, le=MAX_SOURCE_RECORDS)]
SourceFile = Literal["ledger_events.csv", "psp_events.csv", "bank_entries.csv"]


class FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Scope(FrozenModel):
    tenant_id: StrictStr
    merchant_id: StrictStr
    batch_id: StrictStr
    currency: Literal["EUR"]


class SourceReference(FrozenModel):
    file: SourceFile
    record_number: RecordNumber
    event_id: StrictStr
    sha256: Digest


class EvidenceReference(SourceReference):
    evidence_id: EvidenceId


class SourceSnapshot(FrozenModel):
    file: SourceFile
    sha256: Digest
    data_records: Annotated[StrictInt, Field(ge=1, le=MAX_SOURCE_RECORDS)]


class Difference(FrozenModel):
    kind: Literal["provider_event_absent_from_ledger", "ledger_event_absent_from_provider", "event_values_differ"]
    event_id: StrictStr
    ledger_amount_minor: StrictInt | None
    provider_amount_minor: StrictInt | None
    ledger_source: SourceReference | None
    provider_source: SourceReference | None


class Totals(FrozenModel):
    ledger: StrictInt
    provider: StrictInt
    bank: StrictInt


class Comparison(FrozenModel):
    residual_minor: StrictInt
    status: Literal["needs_review", "balanced_on_supplied_events", "balanced_by_total"]


class Comparisons(FrozenModel):
    ledger_to_provider: Comparison
    provider_to_bank: Comparison


class Facts(FrozenModel):
    schema_version: Literal["0.0.1"]
    mode: Literal["deterministic_fixture_comparison"]
    scope: Scope
    totals_minor: Totals
    comparisons: Comparisons
    event_differences: tuple[Difference, ...]
    source_snapshots: tuple[SourceSnapshot, ...]
    review_required: StrictBool
    external_completeness_verified: Literal[False]


class ReconciliationCase(FrozenModel):
    schema_version: Literal["0.1.0"] = "0.1.0"
    case_id: CaseId
    case_version: Digest
    data_classification: Literal["synthetic"] = "synthetic"
    read_only: Literal[True] = True
    facts: Facts
    evidence: tuple[EvidenceReference, ...]


class CaseSummary(FrozenModel):
    case_id: CaseId
    case_version: Digest
    review_required: StrictBool
    currency: Literal["EUR"] = "EUR"
    ledger_to_provider_residual_minor: StrictInt


class CaseList(FrozenModel):
    cases: tuple[CaseSummary, ...]


class SourceRow(FrozenModel):
    tenant_id: StrictStr
    merchant_id: StrictStr
    batch_id: StrictStr
    event_id: StrictStr
    event_type: StrictStr
    amount_eur: StrictStr
    currency: Literal["EUR"]
    effective_at: StrictStr
    description: Annotated[StrictStr, Field(max_length=2048)]


class EvidenceRecord(FrozenModel):
    case_id: CaseId
    case_version: Digest
    reference: EvidenceReference
    row: SourceRow
    data_role: Literal["untrusted_source_data"] = "untrusted_source_data"


class UnknownCaseError(LookupError):
    pass


class UnknownEvidenceError(LookupError):
    pass


class CaseVersionMismatch(ValueError):
    pass


class CaseStore:
    """Load once at startup; all reads use this snapshot until process restart.

    The directory is operator configuration, never an API or MCP argument.
    Only the three allow-listed CSV names are read. Case IDs and evidence IDs
    are looked up in memory, never used to construct a filesystem path.
    This is a single-fixture store, not a tenant authorization mechanism.
    """

    def __init__(self, directory: Path = FIXTURE):
        snapshots = {}
        for filename in SOURCE_FILES:
            path = directory / filename
            if path.is_symlink() or not path.is_file():
                raise InputError(f"{filename}: expected a regular fixture file.")
            with path.open("rb") as handle:
                content = handle.read(MAX_SOURCE_BYTES + 1)
            if len(content) > MAX_SOURCE_BYTES:
                raise InputError(f"{filename}: exceeds the fixture size limit.")
            snapshots[filename] = content

        raw_facts = reconcile_snapshots(snapshots)
        if any(s["data_records"] > MAX_SOURCE_RECORDS for s in raw_facts["source_snapshots"]):
            raise InputError("A source exceeds the fixture record limit.")
        facts = Facts.model_validate(raw_facts)
        canonical = json.dumps(
            {"case_id": CASE_ID, "case_schema_version": "0.1.0", "facts": raw_facts},
            sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        ).encode("utf-8")
        version = sha256(canonical).hexdigest()

        records = {}
        for filename in SOURCE_FILES:
            content = snapshots[filename]
            digest = sha256(content).hexdigest()
            reader = csv.DictReader(StringIO(content.decode("utf-8-sig"), newline=""), strict=True)
            for record_number, row in enumerate(reader, 1):
                identity = json.dumps(
                    [filename, digest, record_number, row["event_id"]], separators=(",", ":")
                ).encode("utf-8")
                reference = EvidenceReference(
                    file=filename, record_number=record_number, event_id=row["event_id"],
                    sha256=digest, evidence_id="ev_" + sha256(identity).hexdigest(),
                )
                records[reference.evidence_id] = EvidenceRecord(
                    case_id=CASE_ID, case_version=version, reference=reference,
                    row=SourceRow.model_validate(row),
                )
        self._case = ReconciliationCase(
            case_id=CASE_ID, case_version=version, facts=facts,
            evidence=tuple(record.reference for record in records.values()),
        )
        self._records = MappingProxyType(records)

    def list_cases(self) -> CaseList:
        case = self._case
        return CaseList(cases=(CaseSummary(
            case_id=case.case_id, case_version=case.case_version,
            review_required=case.facts.review_required,
            ledger_to_provider_residual_minor=case.facts.comparisons.ledger_to_provider.residual_minor,
        ),))

    def get_case(self, case_id: str) -> ReconciliationCase:
        if case_id != self._case.case_id:
            raise UnknownCaseError("Unknown case ID.")
        return self._case

    def get_evidence(self, case_id: str, case_version: str, evidence_id: str) -> EvidenceRecord:
        case = self.get_case(case_id)
        if case_version != case.case_version:
            raise CaseVersionMismatch("Case version changed; retrieve the case again.")
        if evidence_id not in self._records:
            raise UnknownEvidenceError("Unknown evidence ID for this case.")
        return self._records[evidence_id]
