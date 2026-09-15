import pytest
from app import agent
from app.config import Settings
from app.llm.base import LLMMessage, LLMUnavailableError
from app.skills import route_skill, html_document


def test_filtered_document_removes_orphans_and_uses_canonical_sources():
    from app.skills import clean_document, build_artifacts
    draft = '# Activation\n\nSupported lesson. [1]\n\n## Empty section\n\n## Takeaway\n\nApply the lesson. [1]\n\nReferences: [1]\n\nInvented episode title. [1]'
    cleaned = clean_document(draft)
    assert 'Empty section' not in cleaned and 'Invented episode' not in cleaned
    assert '## Takeaway\n\nApply the lesson. [1]' in cleaned
    artifact = build_artifacts('markdown_artifact', draft, [{'guest': 'Real guest', 'title': 'Verified title', 'start_timestamp': '01:00', 'source_url': 'https://example.com/transcript'}])[0]
    assert 'Verified title' in artifact['content']
    assert 'Invented episode' not in artifact['content']
    nested = '# Activation\n\n## Introduction\n\nSupported lesson. [1]'
    assert clean_document(nested+'\n\n[1]') == nested


@pytest.mark.parametrize('question,expected', [
    ('How do growth loops work?', 'grounded_qa'),
    ('Draft a Ship 30 for 30 essay on activation', 'ship_30_for_30'),
    ('Make an HTML one-pager of retention', 'html_artifact'),
    ('Make a Markdown document about that', 'markdown_artifact'),
])
def test_routing(question, expected):
    assert route_skill(question) == expected


def test_followup_preserves_substantive_question_with_pronoun_in_second_clause():
    original = 'What is an activation aha moment, and how did Hila Qu approach it at GitLab?'
    history = [LLMMessage(role='user', content=original), LLMMessage(role='assistant', content='Earlier answer.')]
    query = agent._retrieval_query(history, 'How would I apply that to my team?', 'grounded_qa')
    assert original in query and 'GitLab' in query


def test_essay_rules_and_artifact_persist_after_reload(client, stub_llm):
    import re
    def write_section(system, messages):
        stub_llm.last_system = system
        stub_llm.last_messages = messages
        number = re.search(r'Use only citation \[(\d+)\]', messages[-1].content)[1]
        target = int(re.search(r'approximately (\d+) words', messages[-1].content)[1])
        return '# Activation matters\n\n' + ' '.join(['evidence'] * target) + f' [{number}].'
    stub_llm.generate = write_section
    sid = client.post('/sessions', json={}).json()['id']
    response = client.post(f'/sessions/{sid}/messages', json={'content': 'Draft a Ship 30 essay on activation'})
    message = response.json()['assistant_message']
    assert message['skill'] == 'ship_30_for_30'
    assert '1250' in stub_llm.last_system
    assert 'consistent steps' in stub_llm.last_system
    assert message['artifacts'][0]['type'] == 'markdown'
    assert message['warnings'] == []
    assert client.get(f'/sessions/{sid}/messages').json()[-1]['artifacts'] == message['artifacts']


def test_html_artifact_arrives_before_done(client, stub_llm):
    import json
    stub_llm._reply = '# Retention\n\nUnderstand customer value [1].'
    sid = client.post('/sessions', json={}).json()['id']
    response = client.post(f'/sessions/{sid}/messages/stream', json={'content': 'Make an HTML one-pager on retention'})
    events = [json.loads(line) for line in response.text.splitlines()]
    artifact = next(e['artifact'] for e in events if e['type'] == 'artifact')
    assert artifact['content'].startswith('<!doctype html>')
    assert '<style>' in artifact['content']
    assert events[-1]['type'] == 'done'
    assert client.get(f'/sessions/{sid}/messages').json()[-1]['artifacts'][0] == artifact


def test_unknown_skill_is_rejected_before_persistence(client):
    sid = client.post('/sessions', json={}).json()['id']
    assert client.post(f'/sessions/{sid}/messages', json={'content': 'Question', 'skill': 'unknown'}).status_code == 422
    assert client.get(f'/sessions/{sid}/messages').json() == []


def test_invalid_citation_is_flagged_and_not_used_for_artifact(client, stub_llm):
    stub_llm._reply = '# Draft\nUnsupported reference [99].'
    sid = client.post('/sessions', json={}).json()['id']
    message = client.post(f'/sessions/{sid}/messages', json={'content': 'Make a Markdown document on activation'}).json()['assistant_message']
    assert message['grounded'] is False
    assert message['warnings']
    assert message['artifacts'] == []
    assert message['citations'] == []
    assert 'Unsupported reference' not in message['content']
    assert 'could not verify' in message['content']


def test_empty_retrieval_answers_from_general_knowledge_for_plain_questions(monkeypatch, stub_llm):
    stub_llm._reply = "Hi! I'm the Lenny Growth Assistant."
    class Empty:
        def query(self, question, k): return []
        def is_grounded(self, chunks): return False
    monkeypatch.setattr(agent, 'retriever_for', lambda settings: Empty())
    result = agent.handle_message(Settings(ALLOW_GENERAL_KNOWLEDGE=True), stub_llm, [], 'What is the weather?')
    assert not result.grounded
    assert result.artifacts == []
    assert result.citations == []
    assert result.text == "Hi! I'm the Lenny Growth Assistant."
    assert stub_llm.last_system == agent.GENERAL_SYSTEM_PROMPT
    assert any('general knowledge' in w for w in result.warnings)


def test_generation_timeout_falls_back_to_general_knowledge(monkeypatch):
    """A grounded_qa attempt can time out on a large CPU prompt even when
    retrieval found a passing-similarity chunk. Rather than surfacing a raw
    connection error, retry once with a small, context-free prompt."""
    class Chunk:
        guest, title, text = 'Guest', 'Title', 'evidence text'
        publish_date, start_timestamp = '', '00:00:00'
        youtube_url, deep_link, source_url = '', '', ''
        similarity = 0.5

    class Grounded:
        def query(self, question, k): return [Chunk()]
        def is_grounded(self, chunks): return True

    class FlakyLLM:
        provider_name, model_name = 'flaky', 'flaky-model'

        def __init__(self):
            self.calls = 0

        @property
        def primary(self):
            return self

        def generate(self, system, messages):
            self.calls += 1
            if self.calls == 1:
                raise LLMUnavailableError('simulated timeout')
            return 'Paris is the capital of France.'

    monkeypatch.setattr(agent, 'retriever_for', lambda settings: Grounded())
    result = agent.handle_message(Settings(ALLOW_GENERAL_KNOWLEDGE=True), FlakyLLM(), [],
                                   'What is the capital of France?')
    assert result.grounded is False
    assert result.citations == []
    assert 'Paris' in result.text
    assert any('general knowledge' in w for w in result.warnings)


def test_generation_timeout_without_general_knowledge_shows_raw_error(monkeypatch, stub_llm):
    """Same timeout, but with the flag off (the assignment demo default):
    surface the plain connection error rather than silently switching modes."""
    class Chunk:
        guest, title, text = 'Guest', 'Title', 'evidence text'
        publish_date, start_timestamp = '', '00:00:00'
        youtube_url, deep_link, source_url = '', '', ''
        similarity = 0.5

    class Grounded:
        def query(self, question, k): return [Chunk()]
        def is_grounded(self, chunks): return True

    def always_fails(system, messages):
        raise LLMUnavailableError('simulated timeout')
    stub_llm.generate = always_fails

    monkeypatch.setattr(agent, 'retriever_for', lambda settings: Grounded())
    result = agent.handle_message(Settings(ALLOW_GENERAL_KNOWLEDGE=False), stub_llm, [],
                                   'What is the capital of France?')
    assert result.grounded is False
    assert "couldn't reach" in result.text.lower()


def test_empty_retrieval_refuses_content_skills_without_calling_model(monkeypatch, stub_llm):
    class Empty:
        def query(self, question, k): return []
        def is_grounded(self, chunks): return False
    monkeypatch.setattr(agent, 'retriever_for', lambda settings: Empty())
    result = agent.handle_message(Settings(), stub_llm, [], 'Draft a Ship 30 essay on the weather')
    assert not result.grounded
    assert result.artifacts == []
    assert stub_llm.last_system is None
    assert 'not provide enough' in result.text


def test_followup_retrieval_preserves_previous_topic(monkeypatch, stub_llm):
    class Spy:
        query_text = ''
        def query(self, question, k): self.query_text = question; return []
        def is_grounded(self, chunks): return False
    spy = Spy()
    monkeypatch.setattr(agent, 'retriever_for', lambda settings: spy)
    agent.handle_message(Settings(), stub_llm, [LLMMessage('user', 'How do I measure activation?')], 'Turn that into a document')
    assert 'measure activation' in spy.query_text


def test_multiple_artifact_conversions_keep_the_original_topic():
    history = [
        LLMMessage('user', 'Draft a Ship 30 essay on improving user activation. Use 1250 words.'),
        LLMMessage('assistant', 'Activation essay [1].'),
        LLMMessage('user', 'Turn that activation guidance into an HTML one-pager.'),
        LLMMessage('assistant', 'Activation brief [1].'),
    ]
    assert agent._retrieval_query(history, 'Make a Markdown document summarizing the activation guidance for my team', 'markdown_artifact') == 'improving user activation'


def test_explicit_new_document_topic_replaces_previous_topic():
    history = [LLMMessage('user', 'How can I improve activation?')]
    assert agent._retrieval_query(history, 'Make an HTML one-pager of pricing strategy', 'html_artifact') == 'pricing strategy'


def test_model_html_is_escaped_before_document_rendering():
    document = html_document('# Brief\n<script>alert(1)</script>\n<img src="https://evil.test">')
    assert '<script>' not in document
    assert '<img ' not in document
    assert '&lt;script&gt;' in document


def test_downloaded_artifact_uses_canonical_source_identity_and_url():
    from app.skills import build_artifacts
    sources = [{'guest': 'Real guest', 'title': 'Actual episode', 'start_timestamp': '00:10:00', 'source_url': 'https://github.com/example/transcript.md'}]
    artifact = build_artifacts('markdown_artifact', '# Advice\n\nA supported recommendation [1].', sources)[0]
    assert 'Real guest — Actual episode — 00:10:00' in artifact['content']
    assert sources[0]['source_url'] in artifact['content']


def test_format_instructions_do_not_pollute_topic_retrieval():
    from app.skills import retrieval_topic
    question='Draft a Ship 30 essay on improving user activation. Use 1250 words and headings.'
    assert retrieval_topic(question, 'ship_30_for_30') == 'improving user activation'


def test_unverified_quote_and_percentage_are_detected():
    issues=agent._reference_issues('An expert says "a completely invented long quotation" [1]. Growth is 99% [1].', 'actual source words', 1)
    assert any('quotation' in issue for issue in issues)
    assert any('percentage' in issue for issue in issues)


def test_percentage_validation_matches_complete_values_and_ignores_spacing():
    assert agent._reference_issues('The speaker reported 40 % [1].', 'The speaker reported 40%.', 1) == []
    assert any('percentage' in issue for issue in agent._reference_issues('The rate was 1% [1].', 'The rate was 11%.', 1))


def test_assignment_mode_refuses_empty_evidence_without_model_call(monkeypatch, stub_llm):
    class Empty:
        def query(self, question, k): return []
        def is_grounded(self, chunks): return False
    monkeypatch.setattr(agent, 'retriever_for', lambda settings: Empty())
    result=agent.handle_message(Settings(ALLOW_GENERAL_KNOWLEDGE=False),stub_llm,[],'What is the weather?')
    assert 'not provide enough' in result.text
    assert stub_llm.last_system is None
    assert not result.grounded


def test_essay_section_cannot_cite_a_different_retrieved_source(client, stub_llm):
    import re
    def wrong_source(system, messages):
        match=re.search(r'approximately (\d+) words',messages[-1].content)
        target=int(match[1]) if match else 200
        return '# Draft\n\n' + ' '.join(['detail']*target) + ' [1].'
    stub_llm.generate=wrong_source
    sid=client.post('/sessions',json={}).json()['id']
    result=client.post(f'/sessions/{sid}/messages',json={'content':'Draft a Ship 30 essay on activation'}).json()['assistant_message']
    assert not result['grounded']
    assert result['artifacts']==[]
    assert any('supplied source number' in warning for warning in result['warnings'])


def test_model_refusal_is_not_rewritten_into_an_unsupported_answer(client, stub_llm):
    calls=[]
    def refuse(system, messages):
        calls.append(messages)
        return 'The transcripts do not provide enough information to answer this question.'
    stub_llm.generate=refuse
    sid=client.post('/sessions',json={}).json()['id']
    result=client.post(f'/sessions/{sid}/messages',json={'content':'How do I improve activation?'}).json()['assistant_message']
    assert len(calls)==1
    assert not result['grounded']
    assert result['citations']==[]
    assert result['artifacts']==[]
    assert result['warnings']==[]


def test_essay_formatter_trims_overlong_generated_prose_without_cutting_sentences():
    from app.skills.essay import format_section
    paragraph=' '.join(['supported']*65)+'. [2]'
    result=format_section('# Advice\n\n'+paragraph+'\n\n'+paragraph+'\n\nIn this essay we will explain more.', 'Step 2', 2, 100)
    assert result.startswith('## Step 2: Advice [2]')
    assert result.endswith('. [2]')
    assert len(result.split())<=110
    assert 'In this essay' not in result


def test_writer_cannot_duplicate_the_application_step_heading():
    from app.skills.essay import format_section
    from app.skills import clean_document
    result = format_section('# Core usage\n\n## Step 2: A second heading\n\nSnyk measures fixing vulnerabilities [2].', 'Step 2', 2, 200)
    assert result.count('## Step 2:') == 1
    assert 'Snyk measures' in result
    result = clean_document(format_section('# Fill onboarding gaps\n\n## Suggested Application\n\n* Review the first user experience.', 'Step 4', 4, 200))
    assert result.startswith('## Step 4: Fill onboarding gaps [4]')
    assert '### Suggested Application' in result
    assert '* Review the first user experience.' in result


@pytest.mark.parametrize('skill', ['html_artifact', 'markdown_artifact'])
def test_short_documents_do_not_use_the_full_essay_generation_budget(monkeypatch, skill):
    from app.llm import factory
    from retrieve import RetrievedChunk
    budgets = []
    class Provider:
        provider_name = 'ollama'
        model_name = 'test'
        def generate(self, system, messages):
            if system.startswith('Review numbered draft'):
                return '{"unsupported_ids": []}'
            return '# Onboarding\n\nMake onboarding clear [1].'
    def build(provider, settings):
        budgets.append(settings.LLM_MAX_OUTPUT_TOKENS)
        return Provider()
    chunk = RetrievedChunk('test::0', 'Make onboarding clear.', 'Guest', 'Title', '', '00:00:00', '', 0)
    class Retrieval:
        def query(self, question, k): return [chunk]
        def is_grounded(self, chunks): return True
    monkeypatch.setattr(factory, 'build_client', build)
    from app import evidence_audit
    monkeypatch.setattr(evidence_audit, 'get_verifier', lambda path: type('Verifier', (), {'score': lambda self, evidence, claim: 1.0})())
    monkeypatch.setattr(agent, 'retriever_for', lambda settings: Retrieval())
    settings = Settings(CONTENT_MAX_OUTPUT_TOKENS=2400, DOCUMENT_MAX_OUTPUT_TOKENS=800)
    result = agent.handle_message(settings, factory.RoutedLLMClient(settings), [], 'Summarize onboarding', skill)
    assert budgets == [settings.LLM_MAX_OUTPUT_TOKENS, 800]
    assert result.artifacts[0]['type'] == ('html' if skill == 'html_artifact' else 'markdown')
