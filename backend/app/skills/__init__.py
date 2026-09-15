"""Application skills. These are product writing rules, not coding-agent tools."""
import html
import json
import re
from pathlib import Path

SHIP = json.loads(Path(__file__).with_name('ship_30_for_30.json').read_text())


def route_skill(content: str, explicit: str | None = None) -> str:
    if explicit:
        return explicit
    if re.search(r'\b(ship\s*30|essay)\b', content, re.I):
        return 'ship_30_for_30'
    if re.search(r'\b(html|css|one[- ]pager)\b', content, re.I):
        return 'html_artifact'
    if re.search(r'\b(markdown|document|artifact)\b', content, re.I):
        return 'markdown_artifact'
    return 'grounded_qa'


def writing_instructions(skill: str) -> str:
    if skill == 'ship_30_for_30':
        return '\n'.join(SHIP['principles'] + SHIP['assignment_format'])
    if skill in ('html_artifact', 'markdown_artifact'):
        return ('Create a complete, useful Markdown document with a title, descriptive headings, '
                'practical bullets, and citations. Aim for 300 to 450 words. '
                'Do not output code fences or HTML; the application renders the document as requested.')
    return ('Give a direct explanation followed by practical recommendations when appropriate. '
            'Paraphrase evidence, cite at the end of each recommendation, and finish within 220 words.')


def retrieval_topic(content: str, skill: str) -> str:
    if skill != 'grounded_qa':
        match = re.search(r'\b(?:on|about|explaining|of)\s+(.+?)(?:[.!?]|$)', content, re.I)
        if match:
            return match[1].strip()
    return content


def html_document(markdown: str) -> str:
    """Render a small Markdown subset using escaped text only, with self-contained CSS."""
    def inline(s):
        return re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html.escape(s))
    blocks = []
    for line in markdown.splitlines():
        if not line.strip():
            continue
        heading = re.match(r'^(#{1,6})\s+(.+)', line)
        if heading:
            n = len(heading[1]); blocks.append(f'<h{n}>{inline(heading[2])}</h{n}>')
        elif re.match(r'^\s*[-*]\s+', line):
            blocks.append('<ul><li>' + inline(re.sub(r'^\s*[-*]\s+', '', line)) + '</li></ul>')
        else:
            blocks.append('<p>' + inline(line) + '</p>')
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>Lenny Growth Brief</title><style>'
            'body{margin:0;background:#FCF8F5;color:#0F3040;font:17px/1.65 system-ui,sans-serif}'
            'main{max-width:850px;margin:32px auto;padding:32px;background:white;border-radius:16px}'
            'h1{font-size:2.1rem;line-height:1.2}h2{border-bottom:2px solid #D99B7F;padding-bottom:8px}'
            'strong{color:#A56F63}li{margin:8px 0}@media(max-width:600px){main{margin:0;padding:20px}}'
            '</style></head><body><main>' + '\n'.join(blocks) + '</main></body></html>')


def clean_document(text: str) -> str:
    """Remove incomplete bibliography and headings left empty by source filtering."""
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if re.match(r'^\s*(?:#{1,6}\s*)?(?:References|Sources|Bibliography)\s*:', line, re.I) or re.fullmatch(r'\s*#{1,6}\s+(?:References|Sources|Bibliography)\s*', line, re.I):
            lines = lines[:index]
            break
    kept = []
    for index, line in enumerate(lines):
        if re.fullmatch(r'\s*(?:\[\d+\]\s*)+', line):
            continue
        heading = re.match(r'^(#{1,6})\s+', line)
        if heading:
            following = next((item for item in lines[index+1:] if item.strip()), '')
            next_heading = re.match(r'^(#{1,6})\s+', following)
            if not following or (next_heading and len(next_heading[1]) <= len(heading[1])):
                continue
        kept.append(line)
    return re.sub(r'\n{3,}', '\n\n', '\n'.join(kept)).strip()


def build_artifacts(skill: str, text: str, sources=None) -> list[dict]:
    if skill == 'grounded_qa':
        return []
    text = clean_document(text)
    title = next((line.lstrip('# ').strip() for line in text.splitlines() if line.strip()), 'Growth document')[:100]
    if sources:
        cited = {int(number) for number in re.findall(r'\[(\d+)\]', text)}
        references = [f"- [{i}] {source['guest']} — {source['title']} — {source['start_timestamp']} — {source['source_url']}"
                      for i, source in enumerate(sources, 1) if i in cited]
        if references:
            text += '\n\n## Transcript sources\n\n' + '\n'.join(references)
    return [{'id': 'document', 'title': title, 'type': 'html' if skill == 'html_artifact' else 'markdown',
             'content': html_document(text) if skill == 'html_artifact' else text}]
