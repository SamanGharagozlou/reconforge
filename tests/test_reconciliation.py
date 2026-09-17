import csv
import json
from hashlib import sha256
from pathlib import Path
import shutil
import tempfile
import unittest

from reconforge.reconciliation import FIELDS, InputError, reconcile


FIXTURE = Path(__file__).resolve().parents[1] / "examples" / "invoice_deduction"


class ReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.data = Path(self.temp.name) / "example"
        shutil.copytree(FIXTURE, self.data)

    def rows(self, name):
        with (self.data / name).open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    def write(self, name, rows):
        with (self.data / name).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)

    def test_expected_amounts_and_missing_event(self):
        expected = json.loads((self.data / "expected.json").read_text())
        result = reconcile(self.data)
        self.assertEqual(result["totals_minor"], expected["totals_minor"])
        self.assertEqual(result["comparisons"]["ledger_to_provider"]["residual_minor"], 25000)
        self.assertEqual(result["comparisons"]["provider_to_bank"]["residual_minor"], 0)
        self.assertEqual(len(result["event_differences"]), 1)
        finding = result["event_differences"][0]
        self.assertEqual(finding["event_id"], expected["missing_ledger_event_id"])
        self.assertEqual(finding["provider_amount_minor"], -25000)
        self.assertTrue(result["review_required"])
        self.assertFalse(result["external_completeness_verified"])

    def test_evidence_points_to_exact_provider_snapshot(self):
        result = reconcile(self.data)
        ref = result["event_differences"][0]["provider_source"]
        self.assertEqual(ref["record_number"], 7)
        self.assertEqual(ref["file"], "psp_events.csv")
        self.assertEqual(ref["sha256"], sha256((self.data / ref["file"]).read_bytes()).hexdigest())

    def test_duplicate_event_is_rejected(self):
        rows = self.rows("psp_events.csv")
        self.write("psp_events.csv", rows + [rows[0]])
        with self.assertRaisesRegex(InputError, "duplicate"):
            reconcile(self.data)

    def test_currency_is_not_silently_converted(self):
        rows = self.rows("ledger_events.csv")
        rows[0]["currency"] = "USD"
        self.write("ledger_events.csv", rows)
        with self.assertRaisesRegex(InputError, "only EUR"):
            reconcile(self.data)

    def test_sources_from_different_batches_are_rejected(self):
        rows = self.rows("bank_entries.csv")
        rows[0]["batch_id"] = "another_batch"
        self.write("bank_entries.csv", rows)
        with self.assertRaisesRegex(InputError, "same tenant"):
            reconcile(self.data)

    def test_missing_bank_records_are_not_zero_balance(self):
        self.write("bank_entries.csv", [])
        with self.assertRaisesRegex(InputError, "no data records"):
            reconcile(self.data)

    def test_bank_difference_is_separate_from_ledger_difference(self):
        rows = self.rows("bank_entries.csv")
        rows[0]["amount_eur"] = "115000.00"
        self.write("bank_entries.csv", rows)
        result = reconcile(self.data)
        self.assertEqual(result["comparisons"]["provider_to_bank"]["residual_minor"], 5000)
        self.assertEqual(result["comparisons"]["ledger_to_provider"]["residual_minor"], 25000)

    def test_offsetting_changes_do_not_hide_behind_equal_totals(self):
        rows = self.rows("psp_events.csv")
        rows[0]["amount_eur"] = "49999.00"
        rows[1]["amount_eur"] = "40001.00"
        self.write("ledger_events.csv", rows)
        result = reconcile(self.data)
        self.assertEqual(result["comparisons"]["ledger_to_provider"]["residual_minor"], 0)
        self.assertEqual(len(result["event_differences"]), 2)
        self.assertTrue(result["review_required"])

    def test_equal_supplied_events_preserve_completeness_limit(self):
        self.write("ledger_events.csv", self.rows("psp_events.csv"))
        result = reconcile(self.data)
        self.assertFalse(result["review_required"])
        self.assertFalse(result["external_completeness_verified"])

    def test_timezone_is_required(self):
        rows = self.rows("ledger_events.csv")
        rows[0]["effective_at"] = "2026-09-16T09:00:00"
        self.write("ledger_events.csv", rows)
        with self.assertRaisesRegex(InputError, "timezone"):
            reconcile(self.data)


if __name__ == "__main__":
    unittest.main()
