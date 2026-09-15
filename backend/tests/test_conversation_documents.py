import pytest
from app.skills.documents import conversation_document, is_conversion


@pytest.mark.parametrize('document_request,skill', [
    ('Turn that guidance into an HTML one-pager.', 'html_artifact'),
    ('Make a Markdown document summarizing the activation guidance for my team.', 'markdown_artifact'),
])
def test_conversion_preserves_saved_facts_sources_and_persistence_without_model(client, stub_llm, monkeypatch, document_request, skill):
    from app import agent
    sid = client.post('/sessions', json={}).json()['id']
    stub_llm._reply = '# Activation guidance\n\nA source-backed explanation. [1]\n\n## Next steps\n\n* Review onboarding.'
    original = client.post(f'/sessions/{sid}/messages', json={'content': 'How can I improve activation?'}).json()['assistant_message']
    assert original['grounded']
    def unexpected(*args, **kwargs):
        raise AssertionError('Formatting must not regenerate or retrieve facts.')
    monkeypatch.setattr(agent, 'retriever_for', unexpected)
    stub_llm.generate = unexpected
    response = client.post(f'/sessions/{sid}/messages', json={'content': document_request}).json()['assistant_message']
    assert response['skill'] == skill and response['grounded']
    assert response['citations'] == original['citations']
    assert 'A source-backed explanation. [1]' in response['content']
    assert len(response['artifacts']) == 1
    assert 'Transcript sources' in response['artifacts'][0]['content']
    saved = client.get(f'/sessions/{sid}/messages').json()[-1]
    assert saved['content'] == response['content'] and saved['artifacts'] == response['artifacts']


def test_conversion_does_not_reach_into_another_session(client, stub_llm):
    a = client.post('/sessions', json={}).json()['id']
    client.post(f'/sessions/{a}/messages', json={'content': 'How can I improve activation?'})
    b = client.post('/sessions', json={}).json()['id']
    stub_llm._reply = 'The transcripts do not provide enough information to answer this question.'
    reply = client.post(f'/sessions/{b}/messages', json={'content': 'Turn that into an HTML brief.'}).json()['assistant_message']
    assert not reply['grounded'] and reply['artifacts'] == []


@pytest.mark.parametrize('document_request', ['Make an HTML document about pricing.', 'Turn that into an HTML brief on pricing.'])
def test_explicit_new_topic_does_not_copy_old_answer(document_request):
    assert not is_conversion(document_request, 'html_artifact')


def test_summary_preserves_complete_paragraphs_and_citation_ids_across_sections():
    text = '# Brief\n\nAn opening claim. [3]\n\n## Team habits\n\nTeams fix vulnerabilities. [1]\n\n## Onboarding gaps\n\nDelivery gaps mattered. [5]'
    result = conversation_document(text, max_words=35)
    assert len(result.split()) <= 35
    for paragraph in ('An opening claim. [3]', 'Teams fix vulnerabilities. [1]', 'Delivery gaps mattered. [5]'):
        assert paragraph in result
