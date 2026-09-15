from app.llm.base import LLMClient, LLMMessage, LLMUnavailableError


class AnthropicClient(LLMClient):
    provider_name = "anthropic"

    def __init__(self, api_key: str, model: str, timeout: int = 60):
        self.model_name = model
        self._timeout = timeout
        self._api_key = api_key
        self._client = None
        if api_key:
            import anthropic
            self._client = anthropic.Anthropic(api_key=api_key, timeout=timeout)

    def is_available(self) -> bool:
        return bool(self._api_key and self._client is not None)

    def generate(self, system: str, messages: list[LLMMessage]) -> str:
        if not self.is_available():
            raise LLMUnavailableError("ANTHROPIC_API_KEY not configured")
        try:
            resp = self._client.messages.create(
                model=self.model_name,
                max_tokens=2000,
                system=system,
                messages=[{"role": m.role, "content": m.content} for m in messages],
            )
            return "".join(block.text for block in resp.content if block.type == "text")
        except Exception as e:  # noqa: BLE001 — normalize all provider errors
            raise LLMUnavailableError(f"Anthropic request failed: {e}") from e
