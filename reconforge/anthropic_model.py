"""Optional Anthropic Messages adapter using the existing pinned httpx package.

No automatic retries, custom URLs, redirects, provider error-body logging,
server-side conversation IDs, or fallback to the offline simulator.
"""

import re

import httpx

from .investigation import InvestigationError, canonical_json
from .investigator import MAX_INPUT_BYTES, ModelReply, SYSTEM_PROMPT, parse_object

MESSAGES_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
MAX_OUTPUT_TOKENS = 4096
MAX_RESPONSE_BYTES = 262_144


def _anthropic_tools(tools: list[dict]) -> list[dict]:
    converted = []
    for tool in tools:
        if (not isinstance(tool, dict) or tool.get("type") != "function"
                or not isinstance(tool.get("name"), str)
                or not isinstance(tool.get("parameters"), dict)):
            raise InvestigationError("Invalid internal tool definition for Anthropic.")
        converted.append({
            "name": tool["name"],
            "description": tool.get("description", ""),
            "input_schema": tool["parameters"],
            "strict": True,
        })
    return converted


def _anthropic_messages(history: list[dict]) -> list[dict]:
    messages = []
    for item in history:
        if not isinstance(item, dict):
            raise InvestigationError("Invalid internal model history.")
        if item.get("role") == "user":
            content = item.get("content")
            if not isinstance(content, str):
                raise InvestigationError("Invalid user message in model history.")
            messages.append({"role": "user", "content": content})
            continue
        if item.get("type") == "function_call":
            call_id, name, arguments = item.get("call_id"), item.get("name"), item.get("arguments")
            if not isinstance(call_id, str) or not isinstance(name, str) or not isinstance(arguments, str):
                raise InvestigationError("Invalid function call in model history.")
            messages.append({
                "role": "assistant",
                "content": [{"type": "tool_use", "id": call_id, "name": name,
                             "input": parse_object(arguments)}],
            })
            continue
        if item.get("type") == "function_call_output":
            call_id, output = item.get("call_id"), item.get("output")
            if not isinstance(call_id, str) or not isinstance(output, str):
                raise InvestigationError("Invalid function result in model history.")
            messages.append({
                "role": "user",
                "content": [{"type": "tool_result", "tool_use_id": call_id, "content": output}],
            })
            continue
        raise InvestigationError("Unsupported internal model history item for Anthropic.")
    return messages


class AnthropicMessagesModel:
    mode = "anthropic_live"

    def __init__(self, api_key: str, model: str, *, transport: httpx.AsyncBaseTransport | None = None):
        if not isinstance(api_key, str) or not api_key.strip() or any(c.isspace() for c in api_key):
            raise InvestigationError("Supply a nonempty Anthropic API key without whitespace.")
        if not isinstance(model, str) or not re.fullmatch(r"[a-zA-Z0-9_.:-]{1,128}", model):
            raise InvestigationError("Supply an explicit Anthropic Messages API model ID.")
        self._api_key = api_key
        self.requested_model = model
        self._transport = transport

    async def complete(self, history: list[dict], tools: list[dict]) -> ModelReply:
        payload = {
            "model": self.requested_model,
            "max_tokens": MAX_OUTPUT_TOKENS,
            "system": SYSTEM_PROMPT,
            "messages": _anthropic_messages(history),
            "tools": _anthropic_tools(tools),
            "tool_choice": {"type": "any", "disable_parallel_tool_use": True},
            "thinking": {"type": "disabled"},
        }
        body = canonical_json(payload).encode()
        if len(body) > MAX_INPUT_BYTES:
            raise InvestigationError("The provider request exceeds the input byte budget.")
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(30.0, connect=10.0), transport=self._transport,
                follow_redirects=False, trust_env=False,
            ) as client:
                async with client.stream("POST", MESSAGES_URL, content=body, headers={
                    "Authorization": "Bearer " + self._api_key,
                    "anthropic-version": ANTHROPIC_VERSION,
                    "Content-Type": "application/json",
                }) as response:
                    if response.status_code != 200:
                        guidance = {
                            401: "Check your API key.",
                            403: "Check workspace and model permissions.",
                            429: "Check API quota or rate limits; no retry was made.",
                        }.get(response.status_code, "Check the selected model and API request compatibility.")
                        raise InvestigationError(f"Anthropic returned HTTP {response.status_code}. {guidance}")
                    data = bytearray()
                    async for chunk in response.aiter_bytes():
                        data.extend(chunk)
                        if len(data) > MAX_RESPONSE_BYTES:
                            raise InvestigationError("The provider response exceeds the byte limit.")
        except httpx.HTTPError as exc:
            raise InvestigationError("The Anthropic request failed or timed out; no automatic retry was made.") from exc
        try:
            result = parse_object(bytes(data).decode("utf-8"))
        except UnicodeDecodeError as exc:
            raise InvestigationError("The provider returned invalid UTF-8.") from exc
        if (result.get("type") != "message" or result.get("role") != "assistant"
                or result.get("stop_reason") != "tool_use"):
            raise InvestigationError("The provider did not return the required completed tool call.")
        content, usage, returned_model = result.get("content"), result.get("usage"), result.get("model")
        if not isinstance(content, list) or not isinstance(usage, dict) or not isinstance(returned_model, str):
            raise InvestigationError("The provider response lacks content, model identity, or usage metadata.")
        counts = (usage.get("input_tokens"), usage.get("output_tokens"))
        if any(type(value) is not int or value < 0 for value in counts):
            raise InvestigationError("The provider returned invalid token usage metadata.")
        calls = [block for block in content if isinstance(block, dict) and block.get("type") == "tool_use"]
        if len(calls) != 1 or len(content) != 1:
            raise InvestigationError("Exactly one Anthropic tool call is required per turn.")
        block = calls[0]
        if not isinstance(block.get("id"), str) or not isinstance(block.get("name"), str) or not isinstance(block.get("input"), dict):
            raise InvestigationError("The provider returned an invalid tool call.")
        output = [{
            "type": "function_call",
            "call_id": block["id"],
            "name": block["name"],
            "arguments": canonical_json(block["input"]),
            "status": "completed",
        }]
        return ModelReply(output=output, returned_model=returned_model,
                          input_tokens=counts[0], output_tokens=counts[1])
