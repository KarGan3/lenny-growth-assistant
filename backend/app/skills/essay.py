"""Source-scoped long-form writing keeps small-model context and attribution manageable."""
import re
import time
from app.llm.base import LLMMessage, LLMUnavailableError
from app.llm.factory import RoutedLLMClient
from app.skills import retrieval_topic
from app.evidence_audit import audit_evidence


def format_section(text, role, number, budget):
    """Keep complete prose/bullets and label the section's actual input source."""
    budget += 5  # Allow a few citation markers without dropping an otherwise complete paragraph.
    lines=text.strip().splitlines()
    title='Apply the evidence'
    if lines and (lines[0].startswith('#') or lines[0].startswith('**')):
        title=lines.pop(0).strip('#* ')
        title=re.sub(r'\s*\[\d+\]', '', title)
        title=re.sub(r'^Step\s+\d+[:.\s]*', '', title, flags=re.I)
    # The application supplies one consistent step heading per section.
    lines = [line for line in lines if not re.match(r'^#{1,2}\s+Step\s+\d+\b', line, re.I)]
    if role.startswith('Step '):
        # Application subheadings belong inside this step. A sibling-level
        # heading would make cleanup treat the canonical step as empty.
        lines = [re.sub(r'^#{1,2}\s+', '### ', line) for line in lines]
    if role=='opening':heading=f'# {title} [{number}]'
    elif role=='closing':heading=f'## Takeaway [{number}]'
    else:heading=f'## {role}: {title} [{number}]'
    kept=[]; used=0
    for paragraph in re.split(r'\n\s*\n', '\n'.join(lines)):
        paragraph=paragraph.strip()
        if not paragraph or re.match(r"(?i)^(?:in this essay|by the end of this essay)",paragraph):continue
        if used+len(paragraph.split())<=budget:
            kept.append(paragraph);used+=len(paragraph.split());continue
        units=paragraph.splitlines() if '\n' in paragraph else re.split(r'(?<=[.!?])\s+',paragraph)
        for unit in units:
            if used+len(unit.split())>budget:break
            # Never retain a clipped prose sentence; complete bullet lines are allowed.
            if not re.match(r'^\s*(?:[-*]|\d+[.)])\s',unit) and not re.search(r'[.!?](?:\s*\[\d+\])?$',unit):continue
            kept.append(unit);used+=len(unit.split())
        break
    return heading+'\n\n'+'\n\n'.join(kept)


def generate_essay(llm, system, chunks, question, timeout, validate, on_event=None):
    deadline = time.monotonic() + timeout
    audience = 'B2B product managers' if re.search(r'\bB2B\b', question, re.I) else 'product and growth practitioners'
    question = retrieval_topic(question, 'ship_30_for_30')
    chunks = chunks[:5]
    system = system.replace('Write approximately 1250 words, aiming for 1100 to 1400 words.',
        'The FINISHED essay targets 1250 words. This call writes only ONE short section; obey its smaller word target.')
    parts=[]
    section_issues=[]
    word_targets=[130]+[200]*len(chunks)+[120]
    purposes=['Open with a concrete reader problem and an evidence-based hook; do not introduce the essay.']
    purposes += [f'Write Step {i}: develop one useful recommendation from this speaker\'s evidence. Explain why and how, using short paragraphs and a practical bullet list.' for i in range(1,len(chunks)+1)]
    purposes += ['Finish with a specific actionable takeaway grounded in this evidence. Do not repeat previous sections.']
    indices=[0]+list(range(len(chunks)))+[len(chunks)-1]

    def write(index, target, purpose, role):
        remaining=int(deadline-time.monotonic())
        if remaining<=0: raise LLMUnavailableError('The essay exceeded its writing deadline. Please retry or choose a faster model.')
        client=llm
        source=chunks[index];number=index+1
        evidence=f'[{number}] {source.guest}:\n{source.text[:2200]}'
        prompt=(f'Topic: {question}\nAudience: {audience}\n\nEvidence:\n{evidence}\n\n'
                f'{purpose}\nWrite approximately {target} words. Paraphrase, do not quote. '
                f'Use only citation [{number}], at the end of each factual paragraph. '
                'No numerical percentages or benchmarks. Do not invent source facts. '
                'For reported facts, use only what the labeled speaker actually says. '
                'Do not attribute the interviewer\'s words to the guest or claim unreported causal outcomes. '
                'Label the bullet list "Suggested application" so advice is distinct from observed source facts. '
                'Name the speaker and company in the reported example. Adapt the lesson to the reader\'s product; do not make a security-specific task or timeframe a requirement for every B2B product. '
                'Output just this section, with a descriptive Markdown heading.\n\n'
                'Previous section headings (avoid repeating):\n'+ '\n'.join(p.splitlines()[0] for p in parts))
        messages=[LLMMessage(role='user',content=prompt)]
        if on_event:
            on_event({'type':'status','text':'Writing the next evidence-based essay section…'})
        for attempt in range(2):
            remaining=int(deadline-time.monotonic())
            if remaining <= 0:
                raise LLMUnavailableError('The essay exceeded its writing deadline.')
            if isinstance(llm, RoutedLLMClient):
                attempts = 2 if llm.fallback else 1
                client = RoutedLLMClient(llm.settings.model_copy(update={
                    'LLM_MAX_OUTPUT_TOKENS': max(200, min(400, int(target * 1.7) + 35)),
                    'LLM_TIMEOUT_SECONDS': max(1, min(180, remaining // attempts)),
                }))
            if on_event and hasattr(client,'generate_stream'):
                result=client.generate_stream(system,messages,
                    lambda delta:on_event({'type':'delta','text':delta}),
                    lambda:on_event({'type':'answer','text':'\n\n'.join(parts)+ ('\n\n' if parts else '')}))
            else:
                result=client.generate(system=system,messages=messages)
            result=format_section(result,role,number,target)
            issues=validate(result,evidence,len(chunks))
            citations={int(n) for n in re.findall(r'\[(\d+)\]',result)}
            if citations != {number}:issues.append('Use the supplied source number only.')
            if not issues or attempt==1:break
            if on_event:on_event({'type':'answer','text':'\n\n'.join(parts)+ ('\n\n' if parts else '')})
            messages.append(LLMMessage(role='user',content='Correct this section: '+ ' '.join(issues)+f' Keep approximately {target} words. Paraphrase without quotations.\n\n'+result))
        if issues:
            section_issues.extend(f'Section using source [{number}]: {issue}' for issue in issues)
        if not issues:
            remaining = int(deadline-time.monotonic())
            if remaining <= 0:
                raise LLMUnavailableError('The essay exceeded its writing deadline.')
            if on_event:
                on_event({'type': 'status', 'text': 'Checking this section against its sources…'})
            result, audit_issues, removed = audit_evidence(client, result, {number: f'Episode metadata: {source.guest} — {source.title}\n\n{source.text}'}, remaining)
            result = format_section(result, role, number, target)
            section_issues.extend(audit_issues)
        if client is not llm:llm._used_client.set(client._used_client.get())
        return result.strip()

    roles=['opening']+[f'Step {i}' for i in range(1,len(chunks)+1)]+['closing']
    for index,target,purpose,role in zip(indices,word_targets,purposes,roles):
        if on_event and parts:on_event({'type':'delta','text':'\n\n'})
        parts.append(write(index,target,purpose,role))
        if on_event:on_event({'type':'answer','text':'\n\n'.join(parts)})
    for extra in range(2):
        count=len(' '.join(parts).split())
        if count>=1100:break
        source_index = extra % len(chunks)
        section=write(source_index,min(300,1250-count),
                      'Develop a DIFFERENT practical application of the evidence, without repeating the example or advice already covered. Do not write another conclusion.\nAlready covered:\n' + parts[source_index+1][:1200], 'Put the lesson into practice')
        # Expand the matching source's step instead of adding duplicate steps.
        continuation = section.split('\n', 1)[1].strip()
        parts[source_index+1] += '\n\n### Put the lesson into practice\n\n' + continuation
        if on_event:on_event({'type':'answer','text':'\n\n'.join(parts)})
    return '\n\n'.join(parts), section_issues
