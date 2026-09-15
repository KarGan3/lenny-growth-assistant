"""Run the documented ten-question local evidence set; manual scoring is separate."""
import json
import os
import sys
import time
from pathlib import Path
import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from app.agent import _build_context_block, _retrieval_query
from app.config import Settings
from app.llm.base import LLMMessage
from app.rag_client import retriever_for

questions = [
    'How does Rahul Vohra measure product-market fit?',
    'What is an activation aha moment, and how did Hila Qu approach it at GitLab?',
    'Why does Merci Grace recommend designing onboarding early?',
    'Why does Dan Hockenmaier focus on the first user experience for retention?',
    'What growth gaps did Crystal Widjaja describe at Gojek?',
    'How should a B2B SaaS team approach pricing?',
    'How do growth loops differ from a funnel?',
    'How should a team choose a north-star metric?',
    'How would I apply that to my team?',
    "What is tomorrow's exact weather forecast?",
]
base = os.environ.get('EVALUATION_API_URL', 'http://127.0.0.1:5173/api')
settings = Settings()
retriever = retriever_for(settings)
folder = Path('docs/evaluation')
folder.mkdir(exist_ok=True)
report = []
hila_session = None
selected = {int(number) for number in os.environ.get('EVALUATION_QUESTIONS', '1,2,3,4,5,6,7,8,9,10').split(',')}
if not selected or not selected <= set(range(1, 11)):
    raise ValueError('EVALUATION_QUESTIONS must contain question numbers 1 through 10.')
if 9 in selected:
    selected.add(2)  # A fresh follow-up must retain its actual parent question.
report_path = folder / Path(os.environ.get('EVALUATION_REPORT', 'factual-report.json')).name
with httpx.Client(timeout=400) as client:
    response = client.get(base+'/config')
    response.raise_for_status()
    configuration = response.json()
    local = next(provider for provider in configuration['providers'] if provider['id'] == 'ollama')
    assert local['available'] and local['model'] == settings.OLLAMA_MODEL
    assert not configuration['fallback_provider'], 'Local evaluation requires fallback disabled.'
    for index, question in enumerate(questions, 1):
        if index not in selected:
            continue
        if index == 9:
            session = hila_session
        else:
            response = client.post(base+'/sessions', json={'title': f'Factual check {index}', 'user_metadata': {'purpose': 'documented ten-question local benchmark'}})
            response.raise_for_status()
            session = response.json()['id']
        if index == 2:
            hila_session = session
        history_response = client.get(base+f'/sessions/{session}/messages')
        history_response.raise_for_status()
        history = [LLMMessage(role=m['role'], content=m['content']) for m in history_response.json()]
        query = _retrieval_query(history, question, 'grounded_qa')
        chunks = retriever.query(query, k=settings.RAG_TOP_K)
        context = _build_context_block(chunks, settings.RAG_MAX_CONTEXT_CHARS)
        start = time.monotonic()
        first = None
        answer = ''
        with client.stream('POST', base+f'/sessions/{session}/messages/stream', json={'content': question, 'provider_id': 'ollama'}) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                event = json.loads(line)
                if event['type'] == 'delta' and first is None:
                    first = round(time.monotonic()-start, 1)
                if event['type'] == 'answer':
                    answer = event['text']
                if event['type'] == 'error':
                    raise RuntimeError(event['message'])
        response = client.get(base+f'/sessions/{session}/messages')
        response.raise_for_status()
        saved = response.json()[-1]
        assert saved['content'] == answer and not saved['artifacts']
        response = client.get(base+f'/sessions/{session}')
        response.raise_for_status()
        session_metadata = response.json()
        assert session_metadata['llm_provider'] == 'ollama' and session_metadata['llm_model'] == local['model']
        record = {'number': index, 'question': question, 'session_id': session, 'answer': answer,
                  'provider': session_metadata['llm_provider'], 'model': session_metadata['llm_model'],
                  'first_text_seconds': first, 'total_seconds': round(time.monotonic()-start, 1),
                  'grounded': saved['grounded'], 'warnings': saved['warnings'], 'sources': saved['citations'],
                  'retrieval_query': query, 'context': context, 'manual_score': 'pending'}
        report.append(record)
        temporary = report_path.with_suffix('.json.tmp')
        temporary.write_text(json.dumps(report, indent=2)+'\n')
        temporary.replace(report_path)
        print(json.dumps({k:v for k,v in record.items() if k not in ('answer','context','sources')}), flush=True)
    if 10 in selected:
        assert not report[-1]['grounded'] and not report[-1]['sources']
    print(f'{len(report)} local requests and persistence checks completed. Factual accuracy requires manual claim-by-claim scoring.', flush=True)
