"""Small real local-Q&A check, including a follow-up and a separate off-topic chat."""
import json
import os
import time
from pathlib import Path
import httpx

base = os.environ.get('EVALUATION_API_URL', 'http://127.0.0.1:5173/api')
folder = Path('docs/evaluation')
folder.mkdir(exist_ok=True)
report = []
with httpx.Client(timeout=400) as client:
    sessions = []
    for title in ['Local QA — activation follow-up', 'Local QA — unsupported question']:
        response = client.post(base+'/sessions', json={'title': title, 'user_metadata': {'purpose': 'local QA verification'}})
        response.raise_for_status()
        sessions.append(response.json()['id'])
    cases = [
        (sessions[0], 'What did Lauryn Isford use as Airtable\'s team activation milestone, and why?'),
        (sessions[0], 'How would I apply that to my B2B team?'),
        (sessions[1], 'What is tomorrow\'s exact weather forecast in Bengaluru?'),
    ]
    for index, (session, question) in enumerate(cases, 1):
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
        assert saved['content'] == answer
        assert saved['artifacts'] == []
        record = {'question': question, 'session_id': session, 'first_text_seconds': first,
                  'total_seconds': round(time.monotonic()-start, 1), 'grounded': saved['grounded'],
                  'warnings': saved['warnings'], 'sources': saved['citations'], 'answer': answer}
        report.append(record)
        (folder/'qa-report.json').write_text(json.dumps(report, indent=2)+'\n')
        print(json.dumps({k: v for k, v in record.items() if k not in ('sources', 'answer')}), flush=True)
    first_chat = client.get(base+f'/sessions/{sessions[0]}/messages').json()
    second_chat = client.get(base+f'/sessions/{sessions[1]}/messages').json()
    assert len(first_chat) == 4 and len(second_chat) == 2
    assert {m['id'] for m in first_chat}.isdisjoint({m['id'] for m in second_chat})
    assert all(record['grounded'] and record['sources'] and not record['warnings'] for record in report[:2])
    assert not report[2]['grounded'] and not report[2]['sources']
    print('Local Q&A, follow-up, separate persistence and unsupported-question assertions passed.', flush=True)
