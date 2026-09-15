"""Extractive conversation documents preserve saved prose and source identifiers."""
import re
from app.skills import clean_document, retrieval_topic


def is_conversion(request, skill):
    if skill not in ('html_artifact', 'markdown_artifact'):
        return False
    topic = retrieval_topic(request, skill)
    references = r'\b(that|this|above|previous|conversation)\b'
    if topic != request and not re.search(references, topic, re.I):
        return False  # An explicit new topic still needs retrieval.
    return bool(re.search(references, request, re.I) or re.search(
        r'\bthe\s+(?:\w+\s+){0,3}(guidance|answer|essay|discussion)\b', request, re.I))


def conversation_document(text, max_words=450):
    """Select complete saved paragraphs across sections; never rewrite facts."""
    text = clean_document(text)
    sections = []
    title = 'Conversation brief'
    current = {'heading': '', 'units': []}
    for paragraph in re.split(r'\n\s*\n', text):
        heading = re.fullmatch(r'(#{1,2})\s+(.+)', paragraph)
        if heading:
            if current['units']:
                sections.append(current)
            label = re.sub(r'\s*\[\d+\]', '', heading[2]).strip()
            if len(heading[1]) == 1:
                title = label
                label = ''
            current = {'heading': label, 'units': []}
        elif paragraph.strip() and not paragraph.startswith('#'):
            # Keep cited evidence paragraphs and complete application bullets.
            if re.search(r'\[\d+\]', paragraph) or re.match(r'^[-*]\s', paragraph):
                if re.match(r'^[-*]\s', paragraph):
                    current['units'].extend(line.strip() for line in paragraph.splitlines() if line.strip())
                else:
                    current['units'].append(paragraph.strip())
    if current['units']:
        sections.append(current)
    selected = [[] for section in sections]
    used = len(title.split()) + 1
    seen = set()
    phases = []
    for section in sections:
        facts = [unit for unit in section['units'] if not re.match(r'^[-*]\s', unit)]
        bullets = [unit for unit in section['units'] if re.match(r'^[-*]\s', unit)]
        phases.append([facts[:1], bullets, facts[1:]])
    for phase in range(3):
        for depth in range(max((len(groups[phase]) for groups in phases), default=0)):
            for index, section in enumerate(sections):
                if depth >= len(phases[index][phase]):
                    continue
                unit = phases[index][phase][depth]
                normalized = re.sub(r'\s+', ' ', re.sub(r'\[\d+\]', '', unit)).lower()
                if normalized in seen:
                    continue
                cost = len(unit.split()) + (len(section['heading'].split()) + 1 if not selected[index] and section['heading'] else 0)
                if re.match(r'^[-*]\s', unit):
                    cost += 4  # Markdown heading plus Suggested application.
                if used + cost <= max_words:
                    selected[index].append(unit)
                    used += cost
                    seen.add(normalized)
    output = ['# ' + title]
    for section, units in zip(sections, selected):
        units.sort(key=section['units'].index)
        if units:
            if section['heading']:
                output.append('## ' + section['heading'])
            application = False
            for unit in units:
                if not application and re.match(r'^[-*]\s', unit):
                    output.append('### Suggested application')
                    application = True
                output.append(unit)
    return '\n\n'.join(output)
