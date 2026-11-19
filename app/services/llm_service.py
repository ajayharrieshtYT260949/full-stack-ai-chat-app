from collections.abc import AsyncIterator
from openai import AsyncOpenAI, APIConnectionError, APITimeoutError, InternalServerError, RateLimitError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.config import get_settings

_client = None

def get_client():
    global _client
    cfg = get_settings()
    if not cfg.openai_api_key:
        raise RuntimeError("LLM provider is not configured. Add OPENAI_API_KEY to .env.")
    if _client is None:
        options = {"api_key": cfg.openai_api_key}
        if cfg.openai_base_url:
            options["base_url"] = cfg.openai_base_url
        _client = AsyncOpenAI(**options)
    return _client

@retry(
    retry=retry_if_exception_type((APIConnectionError, APITimeoutError, InternalServerError, RateLimitError)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    reraise=True,
)
async def open_llm_stream(messages):
    cfg = get_settings()
    return await get_client().chat.completions.create(
        model=cfg.openai_model, messages=messages, stream=True, stream_options={"include_usage": True}
    )

async def stream_completion(messages) -> AsyncIterator[dict]:
    stream = await open_llm_stream(messages)
    async for chunk in stream:
        if chunk.choices:
            content = chunk.choices[0].delta.content
            if content:
                yield {"type": "token", "content": content}
        if getattr(chunk, "usage", None):
            yield {"type": "usage", "prompt_tokens": chunk.usage.prompt_tokens or 0,
                   "completion_tokens": chunk.usage.completion_tokens or 0}
