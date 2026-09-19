import json
from hashlib import sha256
from pathlib import Path
import shutil
import tempfile
import unittest

from reconforge.cases import (
    BANK_CASE_ID, BANK_FIXTURE, CASE_ID, FIXTURE, MAX_CASES,
    CaseStore, CaseVersionMismatch, UnknownEvidenceError,
)
from reconforge.reconciliation import InputError, reconcile


class MultiCaseTests(unittest.TestCase):
    def setUp(self):
        self.store = CaseStore()
        self.invoice = self.store.get_case(CASE_ID)
        self.bank = self.store.get_case(BANK_CASE_ID)

    def test_second_fixture_matches_independent_financial_expectations(self):
        expected = json.loads((BANK_FIXTURE / "expected.json").read_text())
        result = reconcile(BANK_FIXTURE)
        self.assertEqual(result["totals_minor"], expected["totals_minor"])
        for comparison in ("ledger_to_provider", "provider_to_bank"):
            self.assertEqual(
                result["comparisons"][comparison]["residual_minor"],
                expected[f"{comparison}_residual_minor"],
            )
            self.assertEqual(result["comparisons"][comparison]["status"], expected[f"{comparison}_status"])
        self.assertEqual(len(result["event_differences"]), expected["event_difference_count"])
        self.assertEqual(result["review_required"], expected["review_required"])
        self.assertEqual(result["external_completeness_verified"], expected["external_completeness_verified"])
        self.assertEqual(self.bank.facts.model_dump(mode="json"), result)

    def test_original_case_version_and_evidence_identifiers_are_preserved(self):
        self.assertEqual(
            self.invoice.case_version,
            "60ad64451f91f9098218b5d745b46d4eb458e28f10ada3672fb8354eecee3424",
        )
        reference = next(ref for ref in self.invoice.evidence if ref.event_id == "evt_invoice_001")
        self.assertEqual(
            reference.evidence_id,
            "ev_6515cd141cb91f62b9bc1bb14a7f0da503a7f4cac515a564388e370e12a6da87",
        )
        self.assertEqual(self.invoice, CaseStore(FIXTURE).get_case(CASE_ID))

    def test_repeated_event_ids_in_different_cases_retrieve_the_correct_bank_row(self):
        for case, amount, fixture in [
            (self.invoice, "115050.00", FIXTURE), (self.bank, "81850.00", BANK_FIXTURE),
        ]:
            with self.subTest(case=case.case_id):
                reference = next(ref for ref in case.evidence if ref.file == "bank_entries.csv")
                self.assertEqual(reference.event_id, "evt_bank_001")
                evidence = self.store.get_evidence(case.case_id, case.case_version, reference.evidence_id)
                self.assertEqual(evidence.case_id, case.case_id)
                self.assertEqual(evidence.row.amount_eur, amount)
                self.assertEqual(evidence.row.batch_id, case.facts.scope.batch_id)
                self.assertEqual(reference.sha256, sha256((fixture / reference.file).read_bytes()).hexdigest())

    def test_evidence_from_a_different_case_is_not_returned(self):
        with self.assertRaises(UnknownEvidenceError):
            self.store.get_evidence(BANK_CASE_ID, self.bank.case_version, self.invoice.evidence[0].evidence_id)
        with self.assertRaises(CaseVersionMismatch):
            self.store.get_evidence(BANK_CASE_ID, self.invoice.case_version, self.bank.evidence[0].evidence_id)

    def test_identical_source_bytes_keep_separate_case_contexts(self):
        other_id = "case_identical_bytes"
        store = CaseStore(fixtures={CASE_ID: FIXTURE, other_id: FIXTURE})
        original, other = store.get_case(CASE_ID), store.get_case(other_id)
        self.assertNotEqual(original.case_version, other.case_version)
        self.assertEqual(original.evidence, other.evidence)
        for case in (original, other):
            evidence = store.get_evidence(case.case_id, case.case_version, case.evidence[0].evidence_id)
            self.assertEqual(evidence.case_id, case.case_id)
            self.assertEqual(evidence.case_version, case.case_version)

    def test_source_edit_changes_only_its_own_case_on_reload(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "bank"
            shutil.copytree(BANK_FIXTURE, directory)
            fixtures = {CASE_ID: FIXTURE, BANK_CASE_ID: directory}
            original = CaseStore(fixtures=fixtures)
            bank = original.get_case(BANK_CASE_ID)
            reference = next(ref for ref in bank.evidence if ref.file == "bank_entries.csv")
            path = directory / "bank_entries.csv"
            path.write_bytes(path.read_bytes().replace(b"81850.00", b"81849.00"))
            current = CaseStore(fixtures=fixtures)
            self.assertEqual(original.get_case(CASE_ID), current.get_case(CASE_ID))
            self.assertNotEqual(bank.case_version, current.get_case(BANK_CASE_ID).case_version)
            self.assertEqual(current.get_case(BANK_CASE_ID).facts.comparisons.provider_to_bank.residual_minor, 15100)
            captured = original.get_evidence(BANK_CASE_ID, bank.case_version, reference.evidence_id)
            self.assertEqual(captured.row.amount_eur, "81850.00")
            with self.assertRaises(CaseVersionMismatch):
                current.get_evidence(BANK_CASE_ID, bank.case_version, reference.evidence_id)

    def test_catalogue_is_bounded_and_case_ids_are_validated(self):
        invalid = [
            {}, {f"case_{i}": FIXTURE for i in range(MAX_CASES + 1)},
            {"../../outside": FIXTURE}, {123: FIXTURE}, {"a" * 81: FIXTURE},
        ]
        for fixtures in invalid:
            with self.subTest(keys=list(fixtures)), self.assertRaises(InputError):
                CaseStore(fixtures=fixtures)
        with self.assertRaises(InputError):
            CaseStore(FIXTURE, fixtures={CASE_ID: FIXTURE})

    def test_invalid_second_case_prevents_store_startup(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "invalid"
            shutil.copytree(BANK_FIXTURE, directory)
            (directory / "bank_entries.csv").write_text("invalid CSV\n")
            with self.assertRaises(InputError):
                CaseStore(fixtures={"case_a_valid": FIXTURE, "case_z_invalid": directory})

    def test_catalogue_order_is_stable_and_source_configuration_is_copied(self):
        fixtures = {CASE_ID: FIXTURE, BANK_CASE_ID: BANK_FIXTURE}
        store = CaseStore(fixtures=fixtures)
        fixtures.clear()
        summaries = store.list_cases().cases
        self.assertEqual([item.case_id for item in summaries], sorted([CASE_ID, BANK_CASE_ID]))
        bank = next(item for item in summaries if item.case_id == BANK_CASE_ID)
        self.assertEqual(bank.ledger_to_provider_residual_minor, 0)
        self.assertEqual(bank.provider_to_bank_residual_minor, 15000)
        self.assertTrue(bank.review_required)
