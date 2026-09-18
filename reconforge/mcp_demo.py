"""Real stdio MCP round trip; no model, API key, or paid service is required."""

import asyncio
import sys
from pathlib import Path

from mcp import Client, StdioServerParameters

from . import __version__
from .cases import CaseList, EvidenceRecord, ReconciliationCase
from .money import format_eur


async def run_round_trip() -> tuple[ReconciliationCase, EvidenceRecord, list[str]]:
    process = StdioServerParameters(
        command=sys.executable, args=["-m", "reconforge.mcp_server"],
        cwd=str(Path(__file__).resolve().parents[1]),
    )
    async with asyncio.timeout(30):
        async with Client(process, raise_exceptions=True, read_timeout_seconds=10) as client:
            discovered = await client.list_tools()
            names = sorted(tool.name for tool in discovered.tools)
            if names != ["get_case", "get_evidence", "list_cases"]:
                raise RuntimeError("Unexpected MCP tool catalogue.")
            listed = await client.call_tool("list_cases", {})
            summary = CaseList.model_validate(listed.structured_content)
            if len(summary.cases) != 1:
                raise RuntimeError("Expected exactly one synthetic case.")
            result = await client.call_tool("get_case", {"case_id": summary.cases[0].case_id})
            case = ReconciliationCase.model_validate(result.structured_content)
            reference = next(
                ref for ref in case.evidence
                if ref.file == "psp_events.csv" and ref.event_id == "evt_invoice_001"
            )
            result = await client.call_tool("get_evidence", {
                "case_id": case.case_id, "case_version": case.case_version,
                "evidence_id": reference.evidence_id,
            })
            evidence = EvidenceRecord.model_validate(result.structured_content)
            if evidence.reference != reference or evidence.case_version != case.case_version:
                raise RuntimeError("Evidence does not belong to the requested case snapshot.")
            if case.facts.comparisons.ledger_to_provider.residual_minor != 25000:
                raise RuntimeError("Unexpected synthetic residual.")
            if evidence.row.amount_eur != "-250.00" or not case.facts.review_required:
                raise RuntimeError("Unexpected evidence or review status.")
            return case, evidence, names


def main() -> None:
    case, evidence, names = asyncio.run(run_round_trip())
    print(f"ReconForge {__version__} — read-only MCP round trip")
    print("Transport: stdio; real MCP client and server")
    print("Tools: " + ", ".join(names))
    print(f"Case: {case.case_id}")
    print("Ledger-to-provider residual: " + format_eur(case.facts.comparisons.ledger_to_provider.residual_minor))
    print("Provider-to-bank residual: " + format_eur(case.facts.comparisons.provider_to_bank.residual_minor))
    print(f"Evidence: {evidence.reference.file}, data record {evidence.reference.record_number}, {evidence.row.event_id}")
    print(f"Source SHA-256: {evidence.reference.sha256}")
    print(f"Case version: {case.case_version}")
    print(f"Review required: {case.facts.review_required}")
    print("External completeness verified: False")
    print("No model calls or financial actions were used.")


if __name__ == "__main__":
    main()
