"""Local-only product evaluation. Keep real generated results for the demo."""
import os
import json
import re
import time
from pathlib import Path
import httpx

base=os.environ.get('EVALUATION_API_URL','http://127.0.0.1:5173/api')
report=[]
Path('docs/evaluation').mkdir(exist_ok=True)
with httpx.Client(timeout=650) as client:
    for _ in range(30):
        try:
            if client.get(base+'/health').status_code==200: break
        except httpx.ConnectError: pass
        time.sleep(1)
    configuration = client.get(base+'/config')
    configuration.raise_for_status()
    configuration = configuration.json()
    local = next(provider for provider in configuration['providers'] if provider['id'] == 'ollama')
    assert local['available'], 'The configured Ollama model must be available.'
    assert not configuration['fallback_provider'], 'Local evaluation requires cloud fallback disabled.'
    questions=[
        'Draft a Ship 30 for 30 essay for B2B product managers on improving user activation. Use approximately 1250 words, an opening hook, consistent practical steps, supported examples, citations, and a useful takeaway.',
        'Turn that activation guidance into an HTML one-pager with practical recommendations and source citations.',
        'Make a Markdown document summarizing the activation guidance for my team with source citations.',
    ]
    mode = os.environ.get('EVALUATION_ONLY')
    start_index = 1
    if mode == 'artifacts':
        report = json.loads(Path('docs/evaluation/local-report.json').read_text())[:1]
        session = report[0]['session_id']
        client.get(base+f'/sessions/{session}/messages').raise_for_status()
        questions = questions[1:]
        start_index = 2
    else:
        created = client.post(base+'/sessions',json={'title':'Local demo — activation essay and artifacts','user_metadata':{'purpose':'assignment evaluation'}})
        created.raise_for_status()
        session = created.json()['id']
        if mode == 'essay': questions = questions[:1]
    for index,question in enumerate(questions,start_index):
        start=time.monotonic(); first=None; answer=''; artifacts=[]; warnings=[]; sources=[]
        with client.stream('POST',base+f'/sessions/{session}/messages/stream',json={'content':question,'provider_id':'ollama'}) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                event=json.loads(line)
                if event['type']=='sources': sources=event['sources']
                if event['type']=='delta' and first is None:
                    first=round(time.monotonic()-start,1); print('First text',index,first,flush=True)
                if event['type']=='answer': answer=event['text']
                if event['type']=='artifact': artifacts.append(event['artifact'])
                if event['type']=='warnings': warnings=event['warnings']
                if event['type']=='error': raise RuntimeError(event['message'])
        record={'question':question,'session_id':session,'first_text_seconds':first,
                'total_seconds':round(time.monotonic()-start,1),'word_count':len(answer.split()),
                'artifacts':len(artifacts),'warnings':warnings,'sources':sources}
        report.append(record)
        Path(f'docs/evaluation/local-{index}.md').write_text(answer+'\n')
        for stale in Path('docs/evaluation').glob(f'artifact-{index}.*'):
            stale.unlink()
        for artifact in artifacts:
            ext='html' if artifact['type']=='html' else 'md'
            Path(f'docs/evaluation/artifact-{index}.{ext}').write_text(artifact['content'])
        saved=client.get(base+f'/sessions/{session}/messages').json()[-1]
        assert saved['artifacts']==artifacts
        assert saved['content']==answer
        metadata=client.get(base+f'/sessions/{session}')
        metadata.raise_for_status()
        metadata=metadata.json()
        assert metadata['llm_provider']=='ollama' and metadata['llm_model']==local['model']
        record.update(provider=metadata['llm_provider'],model=metadata['llm_model'])
        Path('docs/evaluation/local-report.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps({k:v for k,v in record.items() if k!='sources'}),flush=True)
    assert report[0]['artifacts']==1, 'Essay artifact missing'
    assert 1100 <= report[0]['word_count'] <= 1400, 'Essay length outside assignment target'
    assert all(r['artifacts']==1 for r in report), 'Artifact generation missing'
    print('Requested local outputs generated and persisted with passing format assertions.',flush=True)
