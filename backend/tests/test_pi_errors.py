from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.config import Settings
from app.llm.base import LLMMessage, LLMUnavailableError
from app.llm.pi_client import PiClient


def test_billing_failure_has_actionable_message_without_stack_trace():
    settings = Settings(ANTHROPIC_API_KEY='test-key')
    client = PiClient('anthropic', settings, SimpleNamespace(model_name='test-model'))
    failed = SimpleNamespace(returncode=1, stderr='file:///private/bridge.mjs:43 Error: Your credit balance is too low to access the Anthropic API.', stdout='')
    with patch('app.llm.pi_client.subprocess.run', return_value=failed):
        with pytest.raises(LLMUnavailableError) as exc:
            client.generate('System', [LLMMessage(role='user', content='Question')])
    assert 'insufficient API credits' in str(exc.value)
    assert 'Ollama' in str(exc.value)
    assert 'file://' not in str(exc.value)


def test_provider_diagnostics_do_not_log_raw_credentials_or_prompt(caplog):
    settings = Settings(ANTHROPIC_API_KEY='private-test-credential')
    client = PiClient('anthropic', settings, SimpleNamespace(model_name='test-model'))
    error = client._failure('Error: 400 invalid_request_error private-test-credential private-question-text')
    assert 'private-test-credential' not in caplog.text
    assert 'private-question-text' not in caplog.text
    record = next(r for r in caplog.records if r.message == 'Pi provider request failed')
    assert record.fields['status'] == 400
    assert record.fields['category'] == 'provider_request'
    assert 'Check backend logs' in str(error)
