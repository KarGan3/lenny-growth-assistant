from app.llm.base import LLMClient, LLMMessage, LLMUnavailableError


class OpenAIClient(LLMClient):
    provider_name = "openai"

    def __init__(self, api_key: str, model: str, timeout: int = 60):
        self.model_name = model
        self._api_key = api_key
        self._client = None
        if api_key:
            from openai import OpenAI
            self._client = OpenAI(api_key=api_key, timeout=timeout)

    def is_available(self) -> bool:
        return bool(self._api_key and self._client is not None)

    def generate(self, system: str, messages: list[LLMMessage]) -> str:
        if not self.is_available():
            raise LLMUnavailableError("OPENAI_API_KEY not configured")
        try:
            resp = self._client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "system", "content": system}]
                + [{"role": m.role, "content": m.content} for m in messages],
                max_tokens=2000,
            )
            return resp.choices[0].message.content or ""
        except Exception as e:  # noqa: BLE001
            raise LLMUnavailableError(f"OpenAI request failed: {e}") from e
