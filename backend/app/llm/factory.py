from app.config import Settings
from app.llm.base import LLMClient, LLMMessage, LLMUnavailableError
from app.llm.anthropic_client import AnthropicClient
from app.llm.ollama_client import OllamaClient
from app.llm.openai_client import OpenAIClient
from app.logging_config import get_logger
from app.llm.pi_client import PiClient
from contextvars import ContextVar

logger = get_logger(__name__)


def build_client(provider: str, settings: Settings) -> LLMClient:
    return PiClient(provider, settings, build_availability_client(provider, settings))


def build_availability_client(provider: str, settings: Settings) -> LLMClient:
    if provider == "anthropic":
        return AnthropicClient(settings.ANTHROPIC_API_KEY, settings.ANTHROPIC_MODEL, settings.LLM_TIMEOUT_SECONDS)
    if provider == "openai":
        return OpenAIClient(settings.OPENAI_API_KEY, settings.OPENAI_MODEL, settings.LLM_TIMEOUT_SECONDS)
    if provider == "ollama":
        return OllamaClient(settings.OLLAMA_BASE_URL, settings.OLLAMA_MODEL, settings.LLM_TIMEOUT_SECONDS, settings.LLM_MAX_OUTPUT_TOKENS)
    raise ValueError(f"Unknown LLM_PROVIDER: {provider}")


class RoutedLLMClient:
    """
    Wraps the configured primary provider and an optional fallback provider.
    If the primary is unreachable (missing key, connection refused, timeout),
    falls back and logs the degradation instead of failing the request —
    satisfies the "resilience" requirement without hiding the failure from
    logs. If both fail, raises LLMUnavailableError with a message the API
    layer turns into a structured error the frontend can render.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self.primary = build_client(settings.LLM_PROVIDER, settings)
        self._used_client = ContextVar('used_llm_client', default=self.primary)
        self.fallback: LLMClient | None = None
        if settings.LLM_FALLBACK_PROVIDER and settings.LLM_FALLBACK_PROVIDER != settings.LLM_PROVIDER:
            self.fallback = build_client(settings.LLM_FALLBACK_PROVIDER, settings)

    @property
    def active_provider(self) -> str:
        return self.primary.provider_name

    @property
    def active_model(self) -> str:
        return self.primary.model_name

    @property
    def generated_provider(self) -> str:
        return self._used_client.get().provider_name

    @property
    def generated_model(self) -> str:
        return self._used_client.get().model_name

    def generate(self, system: str, messages: list[LLMMessage]) -> str:
        self._used_client.set(self.primary)
        try:
            return self.primary.generate(system, messages)
        except LLMUnavailableError as primary_err:
            logger.warning(
                "primary LLM provider failed, attempting fallback",
                extra={"fields": {"primary_provider": self.primary.provider_name, "error": str(primary_err)}},
            )
            if self.fallback is not None:
                try:
                    text = self.fallback.generate(system, messages)
                    self._used_client.set(self.fallback)
                    logger.info('fallback answered', extra={'fields': {'provider': self.fallback.provider_name, 'model': self.fallback.model_name}})
                    return text
                except LLMUnavailableError as fallback_err:
                    raise LLMUnavailableError(
                        f"Primary provider ({self.primary.provider_name}) failed: {primary_err}. "
                        f"Fallback provider ({self.fallback.provider_name}) also failed: {fallback_err}"
                    ) from fallback_err
            raise

    def generate_stream(self, system, messages, on_delta, on_reset):
        self._used_client.set(self.primary)
        try:
            return self.primary.generate_stream(system, messages, on_delta)
        except LLMUnavailableError as primary_err:
            logger.warning('primary streaming provider failed', extra={'fields': {
                'provider': self.primary.provider_name, 'error': str(primary_err),
                'fallback_provider': self.fallback.provider_name if self.fallback else None,
            }})
            if self.fallback is None:
                raise
            on_reset()
            text = self.fallback.generate_stream(system, messages, on_delta)
            self._used_client.set(self.fallback)
            logger.info('fallback answered', extra={'fields': {'provider': self.fallback.provider_name, 'model': self.fallback.model_name}})
            return text
