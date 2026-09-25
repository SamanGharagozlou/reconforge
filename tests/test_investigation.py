import shutil
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

from reconforge.cases import BANK_CASE_ID, BANK_FIXTURE, CASE_ID, CaseStore
from reconforge.investigation import (
    InvestigationError, proposal_template, required_evidence, validate_context, validate_proposal,
)
from reconforge.reports import get_investigation_report


class InvestigationContractTests(unittest.TestCase):
    def setUp(self):
        self.store = CaseStore()
        self.case = self.store.get_case(BANK_CASE_ID)
        self.report = get_investigation_report(self.store, BANK_CASE_ID, self.case.case_version)
        self.candidate = proposal_template(self.case, self.report)
        self.inspected = {eid: self.store.get_evidence(BANK_CASE_ID, self.case.case_version, eid)
                          for eid in required_evidence(self.report)}

    def validate(self, candidate=None, inspected=None):
        return validate_proposal(self.candidate if candidate is None else candidate, self.case, self.report,
                                 self.inspected if inspected is None else inspected)

    def test_complete_plan_keeps_all_facts_and_allows_different_priorities(self):
        self.candidate['hypothesis_order'].reverse()
        self.candidate['next_step_order'].reverse()
        result = self.validate()
        self.assertEqual(result.findings[4].amount_minor, 15000)
        self.assertEqual(result.hypothesis_order[0], 'adjustment_or_data_error')
        self.assertEqual(result.conclusion, 'cause_undetermined')

    def test_altered_or_coerced_amounts_fail(self):
        for value in (15001, '15000', 15000.0, True, None):
            data = deepcopy(self.candidate)
            data['findings'][4]['amount_minor'] = value
            with self.subTest(value=value), self.assertRaises(InvestigationError):
                self.validate(data)

    def test_missing_duplicate_or_unknown_findings_fail(self):
        candidates = []
        missing = deepcopy(self.candidate); missing['findings'].pop(); candidates.append(missing)
        duplicate = deepcopy(self.candidate); duplicate['findings'][4] = duplicate['findings'][3]; candidates.append(duplicate)
        unknown = deepcopy(self.candidate); unknown['findings'][4]['finding_id'] = 'f_099'; candidates.append(unknown)
        for data in candidates:
            with self.subTest(findings=data['findings']), self.assertRaises(InvestigationError):
                self.validate(data)

    def test_unread_invented_duplicate_and_cross_case_citations_fail(self):
        with self.assertRaises(InvestigationError):
            self.validate(inspected={})
        other = self.store.get_case(CASE_ID).evidence[0].evidence_id
        for ids in (['ev_' + '0' * 64], [other], self.candidate['evidence_ids'] * 2):
            data = dict(self.candidate, evidence_ids=ids)
            with self.subTest(ids=ids), self.assertRaises(InvestigationError):
                self.validate(data)

    def test_reading_an_irrelevant_row_cannot_replace_the_required_bank_row(self):
        ref = next(r for r in self.case.evidence if r.file == 'ledger_events.csv')
        row = self.store.get_evidence(BANK_CASE_ID, self.case.case_version, ref.evidence_id)
        with self.assertRaises(InvestigationError):
            self.validate(dict(self.candidate, evidence_ids=[ref.evidence_id]), {ref.evidence_id: row})

    def test_wrong_case_version_report_and_corrupt_envelope_fail(self):
        for key, value in (('case_id', CASE_ID), ('case_version', '0' * 64), ('report_id', '0' * 64)):
            with self.subTest(key=key), self.assertRaises(InvestigationError):
                self.validate(dict(self.candidate, **{key: value}))
        with self.assertRaises(InvestigationError):
            validate_context(self.case, self.report.model_copy(update={'report_id': '0' * 64}))
        other = self.store.get_case(CASE_ID)
        with self.assertRaises(InvestigationError):
            validate_context(self.case, get_investigation_report(self.store, CASE_ID, other.case_version))

    def test_omitting_unknowns_or_adding_inapplicable_playbook_items_fails(self):
        for key, values in (
            ('question_order', ['bank_difference_cause']),
            ('hypothesis_order', ['ledger_import_or_recording']),
            ('next_step_order', ['obtain_complete_reports', 'inspect_ledger_records']),
            ('hypothesis_order', ['adjustment_or_data_error', 'adjustment_or_data_error']),
        ):
            with self.subTest(key=key, values=values), self.assertRaises(InvestigationError):
                self.validate(dict(self.candidate, **{key: values}))

    def test_invented_causes_free_text_and_financial_actions_are_outside_the_contract(self):
        for key, value in (
            ('conclusion', 'confirmed_bank_fee'), ('conclusion', 'no_discrepancy_in_supplied_records'),
            ('explanation', 'The bank definitely charged a fee.'),
            ('financial_actions_allowed', True), ('post_adjustment', {'amount_minor': 15000}),
        ):
            with self.subTest(key=key), self.assertRaises(InvestigationError):
                self.validate(dict(self.candidate, **{key: value}))

    def test_read_record_from_another_snapshot_is_rejected(self):
        eid = next(iter(self.inspected))
        stale = self.inspected[eid].model_copy(update={'case_version': '0' * 64})
        with self.assertRaises(InvestigationError):
            self.validate(inspected={eid: stale})

    def test_invoice_plan_requires_both_bank_and_missing_event_evidence(self):
        case = self.store.get_case(CASE_ID)
        report = get_investigation_report(self.store, CASE_ID, case.case_version)
        candidate = proposal_template(case, report)
        rows = {eid: self.store.get_evidence(CASE_ID, case.case_version, eid) for eid in required_evidence(report)}
        self.assertEqual({r.reference.file for r in rows.values()}, {'bank_entries.csv', 'psp_events.csv'})
        self.assertEqual(validate_proposal(candidate, case, report, rows).findings[-1].amount_minor, -25000)

    def test_larger_report_is_rejected_before_a_model_call(self):
        with patch('reconforge.investigation.MAX_FINDINGS', 4), self.assertRaises(InvestigationError):
            validate_context(self.case, self.report)

    def test_balanced_case_retains_completeness_question_without_inventing_a_cause(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Path(temporary) / 'balanced'
            shutil.copytree(BANK_FIXTURE, fixture)
            bank = fixture / 'bank_entries.csv'
            bank.write_text(bank.read_text().replace('81850.00', '82000.00'))
            store = CaseStore(fixtures={BANK_CASE_ID: fixture})
            case = store.get_case(BANK_CASE_ID)
            report = get_investigation_report(store, BANK_CASE_ID, case.case_version)
            rows = {eid: store.get_evidence(BANK_CASE_ID, case.case_version, eid)
                    for eid in required_evidence(report)}
            candidate = proposal_template(case, report)
            result = validate_proposal(candidate, case, report, rows)
            self.assertEqual(result.conclusion, 'no_discrepancy_in_supplied_records')
            self.assertEqual(result.hypothesis_order, ())
            self.assertEqual(result.question_order, ('external_completeness',))
