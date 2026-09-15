"""Run the Pi Coding Agent SDK with the grounded prompt prepared by retrieval."""
import json
from pathlib import Path
import subprocess
import os
import select
import tempfile
import time
import re

from app.config import Settings
from app.llm.base import LLMClient, LLMUnavailableError
from app.logging_config import get_logger

logger = get_logger(__name__)


class PiClient(LLMClient):
    def __init__(self, provider: str, settings: Settings, availability_client: LLMClient):
        self.provider_name = provider
        self.model_name = availability_client.model_name
        self.settings = settings
        self.availability_client = availability_client
        self.bridge = Path(__file__).resolve().parents[2] / 'pi-agent' / 'bridge.mjs'

    def is_available(self):
        return (self.bridge.parent / 'node_modules' / '@mariozechner' / 'pi-coding-agent').exists() and self.availability_client.is_available()

    def generate(self, system, messages):
        payload = self._payload(system, messages)
        try:
            result = subprocess.run(['node', str(self.bridge)], input=json.dumps(payload),
                                    capture_output=True, text=True, cwd=self.bridge.parent,
                                    timeout=self.settings.LLM_TIMEOUT_SECONDS)
            if result.returncode:
                raise self._failure(result.stderr)
            return json.loads(result.stdout)['text']
        except (OSError, subprocess.TimeoutExpired, ValueError, KeyError) as exc:
            raise LLMUnavailableError(f'Pi agent ({self.provider_name}) could not complete: {exc}') from exc

    def _failure(self, stderr):
        error = stderr.lower()
        category = 'provider_request'
        if 'credit balance is too low' in error or 'insufficient_quota' in error:
            category = 'billing'
        elif 'authentication_error' in error or 'invalid api key' in error or 'invalid_api_key' in error:
            category = 'authentication'
        elif 'rate_limit' in error:
            category = 'rate_limit'
        status = re.search(r'\b(400|401|403|404|429|500|502|503|504)\b', error)
        # Provider stderr can contain prompts or credentials; log diagnostics,
        # never the raw stack trace or response body.
        logger.error('Pi provider request failed', extra={'fields': {
            'provider': self.provider_name, 'model': self.model_name,
            'category': category, 'status': int(status[1]) if status else None,
        }})
        if 'credit balance is too low' in error or 'insufficient_quota' in error:
            return LLMUnavailableError(f'{self.provider_name} has insufficient API credits. Add credits in the provider billing settings or select Ollama for local answers.')
        if 'authentication_error' in error or 'invalid api key' in error or 'invalid_api_key' in error:
            return LLMUnavailableError(f'{self.provider_name} rejected the API key. Check the key in the root .env file.')
        if 'rate_limit' in error:
            return LLMUnavailableError(f'{self.provider_name} is rate limited. Please wait and try again, or select Ollama.')
        return LLMUnavailableError(f'Pi agent ({self.provider_name}) could not complete the request. Check backend logs for details.')

    def _payload(self, system, messages):
        urls = {'ollama': self.settings.OLLAMA_BASE_URL.rstrip('/') + '/v1',
                'anthropic': 'https://api.anthropic.com', 'openai': 'https://api.openai.com/v1'}
        keys = {'ollama': 'ollama', 'anthropic': self.settings.ANTHROPIC_API_KEY,
                'openai': self.settings.OPENAI_API_KEY}
        if not keys[self.provider_name]:
            raise LLMUnavailableError(f'{self.provider_name} API key is not configured')
        return {'provider': self.provider_name, 'model': self.model_name,
                   'base_url': urls[self.provider_name], 'api_key': keys[self.provider_name],
                   'max_tokens': self.settings.LLM_MAX_OUTPUT_TOKENS,
                   'temperature': self.settings.LLM_TEMPERATURE,
                   'context_length': self.settings.OLLAMA_CONTEXT_LENGTH,
                   'system': system, 'messages': [dict(role=m.role, content=m.content) for m in messages]}

    def generate_stream(self, system, messages, on_delta):
        payload = self._payload(system, messages)
        payload['stream'] = True
        process = None
        with tempfile.TemporaryFile() as errors:
            try:
                process = subprocess.Popen(['node', str(self.bridge)], stdin=subprocess.PIPE,
                                           stdout=subprocess.PIPE, stderr=errors, cwd=self.bridge.parent)
                process.stdin.write(json.dumps(payload).encode())
                process.stdin.close()
                deadline = time.monotonic() + self.settings.LLM_TIMEOUT_SECONDS
                buffer = b''
                answer = None
                while True:
                    on_delta('')  # Also lets a disconnected stream cancel its model process.
                    if time.monotonic() >= deadline:
                        raise LLMUnavailableError('The language model took too long to respond.')
                    ready, _, _ = select.select([process.stdout], [], [], 0.2)
                    if not ready:
                        continue
                    chunk = os.read(process.stdout.fileno(), 65536)
                    if not chunk:
                        break
                    buffer += chunk
                    while b'\n' in buffer:
                        line, buffer = buffer.split(b'\n', 1)
                        event = json.loads(line)
                        if event.get('type') == 'delta':
                            on_delta(event['text'])
                        elif 'text' in event:
                            answer = event['text']
                process.wait(timeout=max(0.1, deadline - time.monotonic()))
                if process.returncode:
                    errors.seek(0)
                    raise self._failure(errors.read().decode(errors='replace'))
                if answer is None:
                    raise LLMUnavailableError('The model stream ended without an answer.')
                return answer
            except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
                raise LLMUnavailableError(f'Pi model stream could not complete: {exc}') from exc
            finally:
                if process is not None:
                    if process.poll() is None:
                        process.kill()
                    process.wait()
                    process.stdout.close()
                    if not process.stdin.closed:
                        process.stdin.close()
