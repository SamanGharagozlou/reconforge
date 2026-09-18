import unittest

from fastapi.testclient import TestClient

from reconforge.api import create_app
from reconforge.cases import CASE_ID, CaseStore


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.store = CaseStore()
        self.client = TestClient(create_app(self.store), base_url="http://127.0.0.1")
        self.addCleanup(self.client.close)
        self.case = self.store.get_case(CASE_ID)

    def test_http_case_matches_the_domain_object(self):
        response = self.client.get(f"/cases/{CASE_ID}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), self.case.model_dump(mode="json"))
        listed = self.client.get("/cases").json()
        self.assertEqual(len(listed["cases"]), 1)
        self.assertEqual(listed["cases"][0]["case_version"], self.case.case_version)

    def test_http_evidence_requires_version_and_returns_correct_row(self):
        reference = next(ref for ref in self.case.evidence if ref.event_id == "evt_invoice_001")
        url = f"/cases/{CASE_ID}/evidence/{reference.evidence_id}"
        self.assertEqual(self.client.get(url).status_code, 422)
        self.assertEqual(self.client.get(url, params={"case_version": "bad"}).status_code, 422)
        self.assertEqual(self.client.get(url, params={"case_version": "0" * 64}).status_code, 409)
        response = self.client.get(url, params={"case_version": self.case.case_version})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["row"]["amount_eur"], "-250.00")
        self.assertEqual(response.json()["reference"]["sha256"], reference.sha256)

    def test_unknown_case_and_evidence_have_explicit_not_found_results(self):
        self.assertEqual(self.client.get("/cases/unknown").status_code, 404)
        response = self.client.get(
            f"/cases/{CASE_ID}/evidence/ev_" + "0" * 64,
            params={"case_version": self.case.case_version},
        )
        self.assertEqual(response.status_code, 404)

    def test_financial_mutations_are_not_exposed(self):
        for method in ["POST", "PUT", "PATCH", "DELETE"]:
            with self.subTest(method=method):
                self.assertEqual(self.client.request(method, f"/cases/{CASE_ID}").status_code, 405)
        self.assertEqual(self.client.post(f"/cases/{CASE_ID}/approve").status_code, 404)

    def test_unexpected_host_is_rejected(self):
        self.assertEqual(self.client.get("/cases", headers={"Host": "untrusted.example"}).status_code, 400)

    def test_openapi_documents_integer_money_and_read_only_routes(self):
        document = self.client.get("/openapi.json").json()
        self.assertEqual(document["components"]["schemas"]["Totals"]["properties"]["ledger"]["type"], "integer")
        for path, operations in document["paths"].items():
            with self.subTest(path=path):
                self.assertEqual(set(operations), {"get"})
