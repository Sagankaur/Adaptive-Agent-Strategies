import json

from llm.async_openai_compatible import AsyncOpenAICompatibleModel


def test_parse_preserves_reasoning_tool_calls_timings_and_cached_tokens():
    client = AsyncOpenAICompatibleModel(base_url="http://localhost:8080/v1", model="local")
    raw = json.dumps(
        {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "reasoning_content": "I should inspect files.",
                        "tool_calls": [
                            {
                                "id": "call-1",
                                "type": "function",
                                "function": {"name": "bash", "arguments": '{"command":"pwd"}'},
                            }
                        ],
                    },
                }
            ],
            "timings": {"prompt_n": 25, "cache_n": 10, "predicted_n": 8, "prompt_ms": 42, "predicted_ms": 16},
            "usage": {
                "prompt_tokens": 25,
                "completion_tokens": 8,
                "prompt_tokens_details": {"cached_tokens": 10},
            },
        }
    ).encode()

    result = client._parse(raw)

    assert result["content"] is None
    assert result["reasoning"] == "I should inspect files."
    assert result["tool_calls"][0].name == "bash"
    assert result["timings"].prompt_tokens == 25
    assert result["timings"].cached_tokens == 10
    assert result["timings"].generated_tokens == 8
    assert result["timings"].prompt_ms == 42
    assert result["timings"].generated_ms == 16


def test_request_serializes_tool_role_and_native_assistant_tool_calls():
    client = AsyncOpenAICompatibleModel(
        base_url="http://localhost:8080/v1",
        model="local",
        chat_template_kwargs={"enable_thinking": True},
    )

    tools = [{"type": "function", "function": {"name": "bash", "parameters": {"type": "object"}}}]
    body = client._request_body(
        [
            {"role": "assistant", "content": None, "tool_calls": [{"id": "call-1", "type": "function"}]},
            {"role": "tool", "content": "done", "tool_call_id": "call-1"},
        ],
        seed=44,
        tools=tools,
    )

    assert body["messages"][0]["tool_calls"][0]["id"] == "call-1"
    assert body["messages"][1]["role"] == "tool"
    assert body["seed"] == 44
    assert body["tools"] == tools
    assert body["chat_template_kwargs"] == {"enable_thinking": True}


def test_per_call_output_limit_lowers_but_never_raises_client_limit():
    client = AsyncOpenAICompatibleModel(base_url="http://localhost:8080/v1", model="local", max_tokens=64)

    lower = client._request_body([{"role": "user", "content": "hello"}], seed=44, max_output_tokens=7)
    higher = client._request_body([{"role": "user", "content": "hello"}], seed=45, max_output_tokens=100)

    assert lower["max_tokens"] == 7
    assert higher["max_tokens"] == 64


def test_explicit_trial_seed_is_used_as_the_root_for_distinct_requests():
    client = AsyncOpenAICompatibleModel(base_url="http://localhost:8080/v1", model="local")

    assert client._next_seed(seed=900) == 900
    assert client._next_seed(seed=900) == 901
