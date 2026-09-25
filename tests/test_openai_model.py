import json
import unittest

import httpx

from reconforge.cases import BANK_CASE_ID, CaseStore
from reconforge.investigation import InvestigationError, proposal_template, required_evidence
from reconforge.investigator import investigate
from reconforge.openai_model import OpenAIResponsesModel, RESPONSES_URL
from reconforge.reports import get_investigation_report


def response(output=None, **updates):
    value = {'status': 'completed', 'model': 'test-model-snapshot',
             'usage': {'input_tokens': 100, 'output_tokens': 20},
             'output': output if output is not None else []}
    value.update(updates)
    return value


class OpenAIAdapterTests(unittest.IsolatedAsyncioTestCase):
    def model(self, handler):
        return OpenAIResponsesModel('unit-test-token', 'test-model', transport=httpx.MockTransport(handler))

    async def test_request_uses_fixed_endpoint_strict_tools_and_no_stored_response(self):
        requests = []
        def handler(request):
            requests.append(request)
            return httpx.Response(200, json=response())
        model = self.model(handler)
        result = await model.complete([{'role': 'user', 'content': 'synthetic data'}], [])
        request = requests[0]
        self.assertEqual(str(request.url), RESPONSES_URL)
        self.assertEqual(request.headers['authorization'], 'Bearer unit-test-token')
        data = json.loads(request.content)
        self.assertFalse(data['store'])
        self.assertFalse(data['parallel_tool_calls'])
        self.assertEqual(data['tool_choice'], 'required')
        self.assertEqual(data['max_output_tokens'], 4096)
        self.assertEqual(data['include'], ['reasoning.encrypted_content'])
        self.assertNotIn('previous_response_id', data)
        self.assertEqual(result.input_tokens, 100)
        self.assertEqual(result.returned_model, 'test-model-snapshot')
        self.assertNotIn('unit-test-token', repr(model))

    async def test_errors_do_not_leak_response_bodies_or_retry(self):
        for status in (400, 401, 403, 429, 500):
            calls = []
            def handler(request):
                calls.append(request)
                return httpx.Response(status, text='unit-test-token PRIVATE-SOURCE-TEXT')
            with self.subTest(status=status), self.assertRaises(InvestigationError) as raised:
                await self.model(handler).complete([], [])
            self.assertNotIn('unit-test-token', str(raised.exception))
            self.assertNotIn('PRIVATE-SOURCE-TEXT', str(raised.exception))
            self.assertEqual(len(calls), 1)

    async def test_redirects_are_not_followed(self):
        calls = []
        def handler(request):
            calls.append(request)
            return httpx.Response(307, headers={'location': 'https://example.invalid/steal'})
        with self.assertRaises(InvestigationError):
            await self.model(handler).complete([], [])
        self.assertEqual(len(calls), 1)

    async def test_timeout_is_redacted_and_not_retried(self):
        calls = []
        def handler(request):
            calls.append(request)
            raise httpx.ReadTimeout('PRIVATE-SOURCE-TEXT unit-test-token', request=request)
        with self.assertRaises(InvestigationError) as raised:
            await self.model(handler).complete([], [])
        self.assertNotIn('PRIVATE-SOURCE-TEXT', str(raised.exception))
        self.assertEqual(len(calls), 1)

    async def test_incomplete_missing_and_coerced_usage_responses_fail(self):
        for data in (response(status='incomplete'), response(usage=None), response(model=None),
                     response(usage={'input_tokens': True, 'output_tokens': 2}),
                     response(usage={'input_tokens': '10', 'output_tokens': 2})):
            with self.subTest(data=data), self.assertRaises(InvestigationError):
                await self.model(lambda req: httpx.Response(200, json=data)).complete([], [])

    async def test_malformed_oversized_and_duplicate_key_responses_fail(self):
        for content in (b'not json', b'\xff', b'x' * 262145,
                        b'{"status":"failed","status":"completed"}', b'[]'):
            with self.subTest(length=len(content)), self.assertRaises(InvestigationError):
                await self.model(lambda req: httpx.Response(200, content=content)).complete([], [])

    async def test_oversized_input_is_blocked_before_network(self):
        calls = []
        def handler(request):
            calls.append(request)
            return httpx.Response(200, json=response())
        with self.assertRaises(InvestigationError):
            await self.model(handler).complete([{'role': 'user', 'content': 'x' * 100000}], [])
        self.assertEqual(calls, [])

    def test_missing_key_and_invalid_model_fail_before_request(self):
        for key, model in (('', 'model'), ('key\nvalue', 'model'), ('key', ''), ('key', 'model\nvalue')):
            with self.subTest(model=model), self.assertRaises(InvestigationError):
                OpenAIResponsesModel(key, model)

    async def test_mock_http_tool_loop_preserves_usage_and_separates_live_mode(self):
        store = CaseStore()
        case = store.get_case(BANK_CASE_ID)
        report = get_investigation_report(store, BANK_CASE_ID, case.case_version)
        eid = next(iter(required_evidence(report)))
        calls = []
        def handler(request):
            calls.append(json.loads(request.content))
            if len(calls) == 1:
                name, args = 'get_evidence', {'evidence_id': eid}
            else:
                name, args = 'submit_investigation', proposal_template(case, report)
            return httpx.Response(200, json=response([{'type': 'function_call', 'call_id': f'call_{len(calls)}',
                                                       'name': name, 'arguments': json.dumps(args), 'status': 'completed'}]))
        async def read(evidence_id):
            return store.get_evidence(BANK_CASE_ID, case.case_version, evidence_id)
        run = await investigate(case, report, self.model(handler), read)
        self.assertEqual(run.mode, 'openai_live')  # HTTP transport mocked; not a live quality result.
        self.assertEqual(run.provider_requests, 2)
        self.assertEqual((run.input_tokens, run.output_tokens), (200, 40))
        self.assertEqual(run.returned_models, ('test-model-snapshot',))
        self.assertEqual(calls[1]['input'][-1]['type'], 'function_call_output')
        self.assertNotIn('unit-test-token', run.model_dump_json())
