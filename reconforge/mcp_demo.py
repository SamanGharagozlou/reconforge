"""Real stdio MCP round trip; no model, API key, or paid service is required."""

import argparse
import asyncio
import sys
from dataclasses import dataclass
from pathlib import Path

from mcp import Client, StdioServerParameters

from . import __version__
from .cases import BANK_CASE_ID, CASE_ID, CaseList, EvidenceRecord, ReconciliationCase
from .money import format_eur


@dataclass(frozen=True)
class DemoExpectation:
    source_file: str
    event_id: str
    row_amount: str
    ledger_residual: int
    bank_residual: int


# Independent assertions for the bundled examples, not reconciliation rules.
DEMOS = {
    CASE_ID: DemoExpectation("psp_events.csv", "evt_invoice_001", "-250.00", 25000, 0),
    BANK_CASE_ID: DemoExpectation("bank_entries.csv", "evt_bank_001", "81850.00", 0, 15000),
}


async def run_round_trip(case_id: str = CASE_ID) -> tuple[ReconciliationCase, EvidenceRecord, list[str]]:
    if case_id not in DEMOS:
        raise ValueError("Choose one of the bundled demonstration case IDs.")
    expected = DEMOS[case_id]
    process = StdioServerParameters(
        command=sys.executable, args=["-m", "reconforge.mcp_server"],
        cwd=str(Path(__file__).resolve().parents[1]),
    )
    async with asyncio.timeout(30):
        async with Client(process, raise_exceptions=True, read_timeout_seconds=10) as client:
            discovered = await client.list_tools()
            names = sorted(tool.name for tool in discovered.tools)
            if names != ["get_case", "get_evidence", "get_investigation_report", "list_cases"]:
                raise RuntimeError("Unexpected MCP tool catalogue.")
            listed = await client.call_tool("list_cases", {})
            summary = CaseList.model_validate(listed.structured_content)
            selected = next((item for item in summary.cases if item.case_id == case_id), None)
            if selected is None:
                raise RuntimeError("The requested synthetic case was not listed.")
            result = await client.call_tool("get_case", {"case_id": selected.case_id})
            case = ReconciliationCase.model_validate(result.structured_content)
            if case.case_id != selected.case_id or case.case_version != selected.case_version:
                raise RuntimeError("Retrieved case does not match its listed snapshot.")
            reference = next(
                ref for ref in case.evidence
                if ref.file == expected.source_file and ref.event_id == expected.event_id
            )
            result = await client.call_tool("get_evidence", {
                "case_id": case.case_id, "case_version": case.case_version,
                "evidence_id": reference.evidence_id,
            })
            evidence = EvidenceRecord.model_validate(result.structured_content)
            if (
                evidence.reference != reference or evidence.case_version != case.case_version
                or evidence.case_id != case.case_id
            ):
                raise RuntimeError("Evidence does not belong to the requested case snapshot.")
            comparisons = case.facts.comparisons
            if (
                comparisons.ledger_to_provider.residual_minor != expected.ledger_residual
                or comparisons.provider_to_bank.residual_minor != expected.bank_residual
                or selected.ledger_to_provider_residual_minor != expected.ledger_residual
                or selected.provider_to_bank_residual_minor != expected.bank_residual
            ):
                raise RuntimeError("Unexpected synthetic residuals.")
            if evidence.row.amount_eur != expected.row_amount or not case.facts.review_required:
                raise RuntimeError("Unexpected evidence or review status.")
            return case, evidence, names


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-id", choices=sorted(DEMOS), default=CASE_ID)
    args = parser.parse_args()
    case, evidence, names = asyncio.run(run_round_trip(args.case_id))
    print(f"ReconForge {__version__} — read-only MCP round trip")
    print("Transport: stdio; real MCP client and server")
    print("Tools: " + ", ".join(names))
    print(f"Case: {case.case_id}")
    print("Ledger-to-provider residual: " + format_eur(case.facts.comparisons.ledger_to_provider.residual_minor))
    print("Provider-to-bank residual: " + format_eur(case.facts.comparisons.provider_to_bank.residual_minor))
    print(f"Evidence: {evidence.reference.file}, data record {evidence.reference.record_number}, {evidence.row.event_id}")
    print(f"Evidence amount: EUR {evidence.row.amount_eur}")
    print(f"Source SHA-256: {evidence.reference.sha256}")
    print(f"Case version: {case.case_version}")
    print(f"Review required: {case.facts.review_required}")
    if case.case_id == BANK_CASE_ID:
        print("The bank payout differs from the provider total; the cause is undetermined.")
    print("External completeness verified: False")
    print("No model calls or financial actions were used.")


if __name__ == "__main__":
    main()
