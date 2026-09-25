import json
import unittest

import httpx

from reconforge.anthropic_model import (
    ANTHROPIC_VERSION, MESSAGES_URL, AnthropicMessagesModel,
)
from reconforge.cases import BANK_CASE_ID, CaseStore
from reconforge.investigation import InvestigationError, proposal_template, required_evidence
from reconforge.investigator import function_tools, investigate
from reconforge.reports import get_investigation_report


def response(content=None, **updates):
    value = {
        "id": "msg_test", "type": "message", "role": "assistant",
        "model": "claude-test-snapshot", "stop_reason": "tool_use",
        "usage": {"input_tokens": 100, "output_tokens": 20},
        "content": content if content is not None else [
            {"type": "tool_use", "id": "toolu_test", "name": "get_evidence",
             "input": {"evidence_id": "ev_" + "0" * 64}},
        ],
    }
    value.update(updates)
    return value


class AnthropicAdapterTests(unittest.IsolatedAsyncioTestCase):
    def model(self, handler):
        return AnthropicMessagesModel("unit-test-token", "claude-test", transport=httpx.MockTransport(handler))

    async def test_request_uses_fixed_endpoint_version_strict_tools_and_single_call_policy(self):
        requests = []
        def handler(request):
            requests.append(request)
            return httpx.Response(200, json=response())
        store = CaseStore()
        case = store.get_case(BANK_CASE_ID)
        report = get_investigation_report(store, BANK_CASE_ID, case.case_version)
        result = await self.model(handler).complete(
            [{"role": "user", "content": "synthetic data"}], function_tools(case, report),
        )
        request = requests[0]
        self.assertEqual(str(request.url), MESSAGES_URL)
        self.assertEqual(request.headers["authorization"], "Bearer unit-test-token")
        self.assertEqual(request.headers["anthropic-version"], ANTHROPIC_VERSION)
        data = json.loads(request.content)
        self.assertEqual(data["tool_choice"], {"type": "any", "disable_parallel_tool_use": True})
        self.assertEqual(data["thinking"], {"type": "disabled"})
        self.assertEqual(data["max_tokens"], 4096)
        self.assertTrue(all(tool["strict"] for tool in data["tools"]))
        self.assertTrue(all("input_schema" in tool and "parameters" not in tool for tool in data["tools"]))
        self.assertEqual(result.input_tokens, 100)
        self.assertEqual(result.returned_model, "claude-test-snapshot")
        self.assertNotIn("unit-test-token", repr(self.model(handler)))

    async def test_history_translates_function_calls_and_results(self):
        requests = []
        def handler(request):
            requests.append(json.loads(request.content))
            return httpx.Response(200, json=response())
        history = [
            {"role": "user", "content": "start"},
            {"type": "function_call", "call_id": "call_1", "name": "get_evidence",
             "arguments": json.dumps({"evidence_id": "ev_" + "1" * 64}), "status": "completed"},
            {"type": "function_call_output", "call_id": "call_1", "output": "{\"ok\":true}"},
        ]
        await self.model(handler).complete(history, [])
        messages = requests[0]["messages"]
        self.assertEqual(messages[1]["content"][0]["type"], "tool_use")
        self.assertEqual(messages[1]["content"][0]["id"], "call_1")
        self.assertEqual(messages[2]["content"][0]["type"], "tool_result")
        self.assertEqual(messages[2]["content"][0]["tool_use_id"], "call_1")

    async def test_errors_do_not_leak_response_bodies_or_retry(self):
        for status in (400, 401, 403, 429, 500):
            calls = []
            def handler(request):
                calls.append(request)
                return httpx.Response(status, text="unit-test-token PRIVATE-SOURCE-TEXT")
            with self.subTest(status=status), self.assertRaises(InvestigationError) as raised:
                await self.model(handler).complete([], [])
            self.assertNotIn("unit-test-token", str(raised.exception))
            self.assertNotIn("PRIVATE-SOURCE-TEXT", str(raised.exception))
            self.assertEqual(len(calls), 1)

    async def test_redirects_are_not_followed(self):
        calls = []
        def handler(request):
            calls.append(request)
            return httpx.Response(307, headers={"location": "https://example.invalid/steal"})
        with self.assertRaises(InvestigationError):
            await self.model(handler).complete([], [])
        self.assertEqual(len(calls), 1)

    async def test_timeout_is_redacted_and_not_retried(self):
        calls = []
        def handler(request):
            calls.append(request)
            raise httpx.ReadTimeout("PRIVATE-SOURCE-TEXT unit-test-token", request=request)
        with self.assertRaises(InvestigationError) as raised:
            await self.model(handler).complete([], [])
        self.assertNotIn("PRIVATE-SOURCE-TEXT", str(raised.exception))
        self.assertEqual(len(calls), 1)

    async def test_refusal_free_text_missing_and_coerced_usage_fail(self):
        cases = [
            response(stop_reason="refusal"),
            response(content=[{"type": "text", "text": "no"}], stop_reason="end_turn"),
            response(usage=None),
            response(model=None),
            response(usage={"input_tokens": True, "output_tokens": 2}),
            response(usage={"input_tokens": "10", "output_tokens": 2}),
        ]
        for data in cases:
            with self.subTest(data=data), self.assertRaises(InvestigationError):
                await self.model(lambda req, data=data: httpx.Response(200, json=data)).complete([], [])

    async def test_multiple_or_malformed_tool_blocks_fail(self):
        bad = [
            response(content=[]),
            response(content=[
                {"type": "tool_use", "id": "a", "name": "get_evidence", "input": {}},
                {"type": "tool_use", "id": "b", "name": "get_evidence", "input": {}},
            ]),
            response(content=[{"type": "tool_use", "id": 7, "name": "get_evidence", "input": {}}]),
            response(content=[{"type": "tool_use", "id": "a", "name": 7, "input": {}}]),
            response(content=[{"type": "tool_use", "id": "a", "name": "get_evidence", "input": []}]),
        ]
        for data in bad:
            with self.subTest(data=data), self.assertRaises(InvestigationError):
                await self.model(lambda req, data=data: httpx.Response(200, json=data)).complete([], [])

    async def test_malformed_oversized_and_duplicate_key_responses_fail(self):
        for content in (b"not json", b"\xff", b"x" * 262145,
                        b'{"type":"message","type":"message"}', b"[]"):
            with self.subTest(length=len(content)), self.assertRaises(InvestigationError):
                await self.model(lambda req, content=content: httpx.Response(200, content=content)).complete([], [])

    async def test_oversized_input_is_blocked_before_network(self):
        calls = []
        def handler(request):
            calls.append(request)
            return httpx.Response(200, json=response())
        with self.assertRaises(InvestigationError):
            await self.model(handler).complete([{"role": "user", "content": "x" * 100000}], [])
        self.assertEqual(calls, [])

    def test_missing_key_and_invalid_model_fail_before_request(self):
        for key, model in (("", "model"), ("key\nvalue", "model"), ("key", ""), ("key", "model\nvalue")):
            with self.subTest(model=model), self.assertRaises(InvestigationError):
                AnthropicMessagesModel(key, model)

    async def test_mock_http_tool_loop_preserves_usage_and_live_mode(self):
        store = CaseStore()
        case = store.get_case(BANK_CASE_ID)
        report = get_investigation_report(store, BANK_CASE_ID, case.case_version)
        eid = next(iter(required_evidence(report)))
        calls = []
        def handler(request):
            calls.append(json.loads(request.content))
            if len(calls) == 1:
                name, args = "get_evidence", {"evidence_id": eid}
            else:
                name, args = "submit_investigation", proposal_template(case, report)
            return httpx.Response(200, json=response([
                {"type": "tool_use", "id": f"toolu_{len(calls)}", "name": name, "input": args},
            ]))
        async def read(evidence_id):
            return store.get_evidence(BANK_CASE_ID, case.case_version, evidence_id)
        run = await investigate(case, report, self.model(handler), read)
        self.assertEqual(run.mode, "anthropic_live")  # HTTP transport mocked; not a live quality result.
        self.assertEqual(run.provider_requests, 2)
        self.assertEqual((run.input_tokens, run.output_tokens), (200, 40))
        self.assertEqual(run.returned_models, ("claude-test-snapshot",))
        self.assertEqual(calls[1]["messages"][-1]["content"][0]["type"], "tool_result")
        self.assertNotIn("unit-test-token", run.model_dump_json())


if __name__ == "__main__":
    unittest.main()
