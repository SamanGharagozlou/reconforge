import csv
from hashlib import sha256
from pathlib import Path
import shutil
import tempfile
import unittest

from pydantic import ValidationError

from reconforge.cases import (
    CASE_ID, FIXTURE, MAX_SOURCE_BYTES, CaseStore, CaseVersionMismatch,
    Totals, UnknownCaseError, UnknownEvidenceError,
)
from reconforge.reconciliation import FIELDS, InputError, reconcile, reconcile_snapshots


class CaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name) / "fixture"
        shutil.copytree(FIXTURE, self.directory)
        self.store = CaseStore(self.directory)
        self.case = self.store.get_case(CASE_ID)
        self.reference = next(
            ref for ref in self.case.evidence
            if ref.file == "psp_events.csv" and ref.event_id == "evt_invoice_001"
        )

    def test_typed_case_preserves_all_baseline_facts(self):
        self.assertEqual(self.case.facts.model_dump(mode="json"), reconcile(self.directory))
        self.assertEqual(len(self.store.list_cases().cases), 1)
        self.assertEqual(self.case, CaseStore(self.directory).get_case(CASE_ID))
        self.assertEqual(len(self.case.evidence), 14)
        self.assertEqual(len({r.evidence_id for r in self.case.evidence}), 14)

    def test_evidence_matches_the_exact_source_row_and_snapshot(self):
        evidence = self.store.get_evidence(CASE_ID, self.case.case_version, self.reference.evidence_id)
        content = (self.directory / "psp_events.csv").read_bytes()
        with (self.directory / "psp_events.csv").open(newline="") as handle:
            row = list(csv.DictReader(handle))[6]
        self.assertEqual(evidence.row.model_dump(), row)
        self.assertEqual(evidence.reference.record_number, 7)
        self.assertEqual(evidence.reference.sha256, sha256(content).hexdigest())
        self.assertEqual(evidence.row.amount_eur, "-250.00")
        self.assertEqual(evidence.data_role, "untrusted_source_data")

    def test_source_edit_cannot_change_an_existing_case_or_its_evidence(self):
        path = self.directory / "psp_events.csv"
        original = path.read_bytes()
        path.write_bytes(original.replace(b"-250.00", b"-300.00"))
        old = self.store.get_evidence(CASE_ID, self.case.case_version, self.reference.evidence_id)
        self.assertEqual(old.row.amount_eur, "-250.00")
        self.assertEqual(old.reference.sha256, sha256(original).hexdigest())
        new_store = CaseStore(self.directory)
        new_case = new_store.get_case(CASE_ID)
        self.assertNotEqual(new_case.case_version, self.case.case_version)
        self.assertEqual(new_case.facts.comparisons.ledger_to_provider.residual_minor, 30000)
        with self.assertRaises(CaseVersionMismatch):
            new_store.get_evidence(CASE_ID, self.case.case_version, self.reference.evidence_id)

    def test_unknown_ids_never_become_file_paths(self):
        for case_id in ["unknown", "../../etc/passwd", "/etc/passwd"]:
            with self.subTest(case_id=case_id), self.assertRaises(UnknownCaseError):
                self.store.get_case(case_id)
        for evidence_id in ["ev_" + "0" * 64, "../../etc/passwd", "psp_events.csv"]:
            with self.subTest(evidence_id=evidence_id), self.assertRaises(UnknownEvidenceError):
                self.store.get_evidence(CASE_ID, self.case.case_version, evidence_id)

    def test_evidence_requires_the_current_case_version(self):
        with self.assertRaises(CaseVersionMismatch):
            self.store.get_evidence(CASE_ID, "0" * 64, self.reference.evidence_id)

    def test_case_and_nested_evidence_are_frozen(self):
        evidence = self.store.get_evidence(CASE_ID, self.case.case_version, self.reference.evidence_id)
        with self.assertRaises(ValidationError):
            evidence.row.amount_eur = "0.00"
        with self.assertRaises(ValidationError):
            self.case.facts.totals_minor.ledger = 0

    def test_transport_money_schema_rejects_float_and_boolean_cents(self):
        for value in [250.0, True, "250"]:
            with self.subTest(value=value), self.assertRaises(ValidationError):
                Totals(ledger=value, provider=250, bank=250)

    def test_large_source_is_rejected_before_parsing(self):
        (self.directory / "psp_events.csv").write_bytes(b"x" * (MAX_SOURCE_BYTES + 1))
        with self.assertRaisesRegex(InputError, "size limit"):
            CaseStore(self.directory)

    def test_record_limit_is_enforced(self):
        with (self.directory / "psp_events.csv").open(newline="") as handle:
            example = next(csv.DictReader(handle))
        with (self.directory / "psp_events.csv").open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(dict(example, event_id=f"evt_{n}") for n in range(1001))
        with self.assertRaisesRegex(InputError, "record limit"):
            CaseStore(self.directory)

    def test_symlink_source_is_rejected(self):
        path = self.directory / "psp_events.csv"
        path.unlink()
        path.symlink_to(FIXTURE / "psp_events.csv")
        with self.assertRaisesRegex(InputError, "regular fixture file"):
            CaseStore(self.directory)

    def test_snapshot_input_requires_all_three_known_sources(self):
        with self.assertRaises(InputError):
            reconcile_snapshots({"unrelated.csv": b""})
