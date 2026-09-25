"""Optional OpenAI Responses adapter using the existing pinned httpx package.

No automatic retries, custom URLs, redirects, provider error-body logging,
server-side conversation IDs, or fallback to the offline simulator.
"""

import re

import httpx

from .investigation import InvestigationError, canonical_json
from .investigator import MAX_INPUT_BYTES, ModelReply, SYSTEM_PROMPT, parse_object

RESPONSES_URL = "https://api.openai.com/v1/responses"
MAX_OUTPUT_TOKENS = 4096
MAX_RESPONSE_BYTES = 262_144


class OpenAIResponsesModel:
    mode = "openai_live"

    def __init__(self, api_key: str, model: str, *, transport: httpx.AsyncBaseTransport | None = None):
        if not isinstance(api_key, str) or not api_key.strip() or any(c.isspace() for c in api_key):
            raise InvestigationError("Supply a nonempty OpenAI API key without whitespace.")
        if not isinstance(model, str) or not re.fullmatch(r"[a-zA-Z0-9_.:-]{1,128}", model):
            raise InvestigationError("Supply an explicit API model ID supporting Responses function calling.")
        self._api_key = api_key
        self.requested_model = model
        self._transport = transport

    async def complete(self, history: list[dict], tools: list[dict]) -> ModelReply:
        payload = {
            "model": self.requested_model, "instructions": SYSTEM_PROMPT,
            "input": history, "tools": tools, "tool_choice": "required",
            "parallel_tool_calls": False, "max_output_tokens": MAX_OUTPUT_TOKENS,
            "store": False, "include": ["reasoning.encrypted_content"],
        }
        body = canonical_json(payload).encode()
        if len(body) > MAX_INPUT_BYTES:
            raise InvestigationError("The provider request exceeds the input byte budget.")
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(30.0, connect=10.0), transport=self._transport,
                follow_redirects=False, trust_env=False,
            ) as client:
                async with client.stream("POST", RESPONSES_URL, content=body, headers={
                    "Authorization": "Bearer " + self._api_key, "Content-Type": "application/json",
                }) as response:
                    if response.status_code != 200:
                        # Error bodies may echo prompts or credentials. Do not print them.
                        guidance = {401: "Check your API key.", 403: "Check project and model permissions.",
                                    429: "Check API quota or rate limits; no retry was made."}.get(
                                        response.status_code, "Check the selected model and API request compatibility.")
                        raise InvestigationError(f"OpenAI returned HTTP {response.status_code}. {guidance}")
                    data = bytearray()
                    async for chunk in response.aiter_bytes():
                        data.extend(chunk)
                        if len(data) > MAX_RESPONSE_BYTES:
                            raise InvestigationError("The provider response exceeds the byte limit.")
        except httpx.HTTPError as exc:
            raise InvestigationError("The OpenAI request failed or timed out; no automatic retry was made.") from exc
        try:
            result = parse_object(bytes(data).decode("utf-8"))
        except UnicodeDecodeError as exc:
            raise InvestigationError("The provider returned invalid UTF-8.") from exc
        if result.get("status") != "completed":
            raise InvestigationError("The provider response was incomplete or failed; no plan was accepted.")
        output, usage, returned_model = result.get("output"), result.get("usage"), result.get("model")
        if not isinstance(output, list) or not isinstance(usage, dict) or not isinstance(returned_model, str):
            raise InvestigationError("The provider response lacks output, model identity, or usage metadata.")
        counts = (usage.get("input_tokens"), usage.get("output_tokens"))
        if any(type(value) is not int or value < 0 for value in counts):
            raise InvestigationError("The provider returned invalid token usage metadata.")
        return ModelReply(output=output, returned_model=returned_model,
                          input_tokens=counts[0], output_tokens=counts[1])
