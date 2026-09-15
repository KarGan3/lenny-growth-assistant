"""Local entailment audit removes unsupported complete units, never writes replacement facts."""
import json
import re
from decimal import Decimal
from app.llm.factory import RoutedLLMClient
from app.logging_config import get_logger

logger = get_logger(__name__)

def draft_units(draft):
    """Number complete prose sentences, headings and whole list items, preserving spans."""
    units = []
    for paragraph in re.finditer(r'\S.*?(?=\n\s*\n|\Z)', draft, re.S):
        text = paragraph.group()
        if text.startswith('#'):
            spans = [(0, len(text))]
        elif re.match(r'^(?:[-*]|\d+[.)])\s', text):
            starts = [m.start() for m in re.finditer(r'(?m)^(?:[-*]|\d+[.)])\s', text)]
            spans = list(zip(starts, starts[1:] + [len(text)]))
        else:
            spans = [(m.start(), m.end()) for m in re.finditer(r'.+?(?:[.!?](?:\s*\[\d+\])?(?=\s|\Z)|\Z)', text, re.S)]
        for start, end in spans:
            raw = text[start:end]
            if raw.strip():
                units.append({'id': len(units), 'text': raw.strip(),
                              'start': paragraph.start()+start, 'end': paragraph.start()+end})
    return units


def apply_audit(draft, response):
    """Validate IDs and delete only the corresponding whole draft units."""
    raw = response.strip()
    if raw.startswith('```'):
        raw = re.sub(r'^```(?:json)?\s*|\s*```$', '', raw).strip()
    units = draft_units(draft)
    try:
        result = json.loads(raw)
        rejected = result['unsupported_ids']
        if not isinstance(rejected, list) or any(type(i) is not int or i < 0 or i >= len(units) for i in rejected):
            raise ValueError('Invalid unit IDs')
        updated = draft
        for index in sorted(set(rejected), reverse=True):
            unit = units[index]
            updated = updated[:unit['start']] + updated[unit['end']:]
        updated = re.sub(r'\n[ \t]*\n(?:[ \t]*\n)+', '\n\n', updated).strip()
        return updated, [], len(set(rejected))
    except (ValueError, KeyError, TypeError):
        return draft, ['The source audit could not be completed reliably. Verify this draft against its excerpts before using it.'], 0


class EvidenceVerifier:
    def __init__(self, model_dir):
        import numpy as np
        import onnxruntime as ort
        from tokenizers import Tokenizer
        from pathlib import Path
        options = ort.SessionOptions()
        options.intra_op_num_threads = 2
        options.inter_op_num_threads = 1
        options.log_severity_level = 3
        ort.disable_telemetry_events()
        folder = Path(model_dir)
        config = json.loads((folder / 'config.json').read_text())
        self.entailment = int(config['label2id']['entailment'])
        self.session = ort.InferenceSession(str(folder / 'model.onnx'), sess_options=options, providers=['CPUExecutionProvider'])
        self.tokenizer = Tokenizer.from_file(str(folder / 'tokenizer.json'))
        self.tokenizer.enable_truncation(max_length=512)
        self.np = np

    def score(self, evidence, claim):
        words = evidence.split()
        prefix = ' '.join(words[:80])
        best = 0.0
        for start in range(0, len(words), 140):
            premise = prefix + '\n' + ' '.join(words[start:start+200])
            encoded = self.tokenizer.encode(premise, claim)
            feeds = {'input_ids': self.np.array([encoded.ids], dtype=self.np.int64),
                     'attention_mask': self.np.array([encoded.attention_mask], dtype=self.np.int64)}
            logits = self.session.run(None, feeds)[0][0]
            probabilities = self.np.exp(logits - logits.max())
            probabilities /= probabilities.sum()
            best = max(best, float(probabilities[self.entailment]))
        return best


from functools import lru_cache


@lru_cache(maxsize=1)
def get_verifier(model_dir):
    return EvidenceVerifier(model_dir)


def evidence_ready(settings):
    try:
        get_verifier(settings.EVIDENCE_MODEL_DIR)
        return True
    except Exception:
        return False


def speaker_passages(text):
    turns = list(re.finditer(r'(?m)^([^\n():]{1,60})\s+\(\d{1,2}:\d{2}(?::\d{2})?\):\s*', text))
    metadata = text[:turns[0].start()] if turns and text.startswith('Episode metadata:') else ''
    return [(turn.group(1).strip(), metadata + text[turn.start():turns[i+1].start() if i+1 < len(turns) else len(text)])
            for i, turn in enumerate(turns)]


def asserted_actors(text, actors):
    names = {name for name in actors if re.search(r'\b'+re.escape(name)+r'\b', text, re.I)}
    names.update(re.findall(r'\bAccording to ([A-Z][\w\x27’\-]*(?: [A-Z][\w\x27’\-]*){0,3})', text))
    match = re.match(r'^([A-Z][\w\x27’\-]*(?: [A-Z][\w\x27’\-]*){1,2})(?=,|\x27s|’s|\s+(?:from|at|says|notes|highlights|emphasizes|describes))', text)
    if match and match[1].split()[0] not in {'In', 'At', 'For', 'As', 'When', 'This', 'The'}:
        names.add(match[1])
    return names


def explicit_details_supported(passage, claim):
    """Check literal details that an entailment score can overlook."""
    aliases = {'PR': 'pull request', 'PMF': 'product market fit', 'PLG': 'product led growth',
               'UX': 'user experience', 'UI': 'user interface', 'API': 'application programming interface',
               'KPI': 'key performance indicator', 'NPS': 'net promoter score', 'NSM': 'north star metric'}
    normalized = re.sub(r'\W+', ' ', passage).lower()
    for entity in re.findall(r'\b(?:at|from|in|including|like)\s+([A-Z][\w-]*(?:\s+[A-Z][\w-]*){0,2})', claim):
        if entity.split()[0] in {'This', 'That', 'The', 'Your', 'Our'}:
            continue
        expanded = aliases.get(entity)
        entity = re.sub(r'\W+', ' ', entity).lower()
        if not re.search(r'\b'+re.escape(entity)+r'\b', normalized) and not (expanded and expanded in normalized):
            return False
    for abbreviation in re.findall(r'\b[A-Z][A-Z0-9]{1,5}\b', claim):
        if not re.search(r'\b'+re.escape(abbreviation.lower())+r'\b', normalized):
            expanded = aliases.get(abbreviation)
            if not expanded or expanded not in normalized:
                return False
    words = dict(zip('zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen'.split(), map(str, range(20))))
    words.update(dict(zip('twenty thirty forty fifty sixty seventy eighty ninety'.split(), map(str, range(20, 100, 10)))))
    def numbers(text):
        return re.sub(r'\b(?:'+ '|'.join(words)+r')\b', lambda match: words[match[0].lower()], text, flags=re.I)
    passage_numbers, claim_numbers = numbers(passage), numbers(claim)
    percent = r'(?<![\w.])([+-]?\d+(?:\.\d+)?)\s*(?:%|percent\b)'
    if not {Decimal(value) for value in re.findall(percent, claim_numbers)} <= {Decimal(value) for value in re.findall(percent, passage_numbers)}:
        return False
    windows = re.findall(r'\b(\d+)\s*[- ]?\s*(day|week|month|year|hour|minute)s?\s+(conversion|retention)', claim_numbers, re.I)
    for value, unit, metric in windows:
        if not re.search(r'\b'+value+r'\s*[- ]?\s*'+unit+r's?\s+'+metric+r'\b', passage_numbers, re.I):
            return False
    corrections = re.finditer(r'\bnot\s+(\d+)\s*[- ]?\s*(day|week|month|year|hour|minute)s?[,\s]+(\d+)\s*[- ]?\s*\2s?\s+(conversion|retention)', passage_numbers, re.I)
    for correction in corrections:
        withdrawn, unit, replacement, metric = correction.groups()
        if withdrawn != replacement and re.search(r'\b'+withdrawn+r'\s*[- ]?\s*'+unit+r's?\s+'+metric+r'\b', claim_numbers, re.I):
            return False
    return True


def audit_evidence(llm, draft, evidence, timeout=90):
    if not isinstance(llm, RoutedLLMClient):
        return draft, [], 0
    import time
    deadline = time.monotonic() + timeout
    try:
        verifier = get_verifier(llm.settings.EVIDENCE_MODEL_DIR)
        passages = {number: speaker_passages(text) for number, text in evidence.items()}
        actors = {name for turns in passages.values() for name, text in turns}
        rejected = []
        verified_citations = {}
        repaired_units = {}
        proposed = False
        for unit in draft_units(draft):
            text = unit['text']
            heading = text.strip('#* :').lower()
            reported = bool(re.search(r'\b(was|were|had|reported|found|increased|doubled|used|achieved|helped|boosted|improved|caused|reduced|grew)\b', text, re.I))
            if text.startswith('#') or heading == 'suggested application':
                proposed = bool(re.search(r'suggested application|practical recommendations|next steps|recommended actions', heading))
                if not reported:
                    continue
            named = asserted_actors(text, actors)
            reported = reported or bool(named)
            if time.monotonic() >= deadline:
                raise TimeoutError('Source audit deadline')
            # Reader framing and clearly marked proposals are not reports of facts.
            if proposed and not reported:
                continue
            if not reported and re.match(r"(?i)^(?:as (?:a|an) |you (?:want|may|might|need) |to (?:apply|improve|define|measure|effectively) |when (?:designing|choosing) |it(?:'s| is) (?:essential|important) |suggested application)", text):
                continue
            # Generated bibliographic text is replaced by canonical source metadata in artifacts.
            if re.match(r'^\[\d+\]\s', text) and '—' in text and not reported:
                rejected.append(unit['id'])
                continue
            cited = {int(n) for n in re.findall(r'\[(\d+)\]', text)}
            candidates = cited or set(evidence)
            claim = re.sub(r'\[\d+\]', '', text).strip()
            selected = [(number, evidence[number]) for number in candidates if number in evidence]
            if named:
                owned = []
                for name in named:
                    matches = [(number, passage) for number in candidates for speaker, passage in passages.get(number, [])
                               if speaker.lower() == name.lower() or speaker.lower().startswith(name.lower()+' ')
                               or speaker.lower().endswith(' '+name.lower())]
                    if not matches:
                        owned = []
                        break
                    owned.extend(matches)
                selected = owned
            # These source-specific states/scopes must be explicitly anchored;
            # generic entailment models can overlook an unsupported qualifier.
            qualifiers = [word for word in ('inactive', 'B2B', 'B2C') if re.search(r'\b'+word+r'\b', claim, re.I)]
            selected = [(number, passage) for number, passage in selected if all(re.search(r'\b'+word+r'\b', passage, re.I) for word in qualifiers)]
            # Tactics that move a metric are not automatically its definition.
            # A definition claim needs explicit measurement language in the
            # guest's own turns, rather than an interviewer's question or title.
            if re.search(r'\bmetric\b.*\b(?:components|defined|calculated|consists)\b', claim, re.I):
                anchored = []
                for number, passage in selected:
                    guest = re.match(r'Episode metadata: (.*?) —', evidence[number])
                    own = [turn for speaker, turn in passages.get(number, []) if not guest or
                           speaker.lower() == guest[1].lower() or speaker.lower().startswith(guest[1].lower()+' ')]
                    body = '\n'.join(re.sub(r'^Episode metadata:[^\n]*\n*', '', turn) for turn in own)
                    if re.search(r'\b(?:metric|measure|measurement|definition|defined|criteria|components)\b', body, re.I):
                        anchored.append((number, passage))
                selected = anchored
            selected = [(number, passage) for number, passage in selected if explicit_details_supported(passage, claim)]
            matches = [(verifier.score(passage, claim), number) for number, passage in selected]
            score, source_number = max(matches, default=(0, None))
            if score < llm.settings.EVIDENCE_MIN_ENTAILMENT:
                repaired = False
                if cited and set(evidence) - cited:
                    raw = draft[unit['start']:unit['end']]
                    uncited = re.sub(r'\s*\[\d+\]', '', raw)
                    candidate, candidate_issues, candidate_removed = audit_evidence(llm, uncited, evidence, max(0, deadline-time.monotonic()))
                    same_prose = lambda value: re.sub(r'\s+', ' ', re.sub(r'\s*\[\d+\]', '', value)).strip()
                    if not candidate_issues and not candidate_removed and re.search(r'\[\d+\]', candidate) and same_prose(candidate) == same_prose(raw):
                        leading = re.match(r'\s*', raw)[0]
                        trailing = re.search(r'\s*$', raw)[0]
                        repaired_units[unit['id']] = leading + candidate.strip() + trailing
                        repaired = True
                if not repaired:
                    rejected.append(unit['id'])
            elif not cited:
                verified_citations[unit['id']] = source_number
        updated, issues, removed = apply_audit(draft, json.dumps({'unsupported_ids': rejected}))
        # Add only source identifiers supported by the checker, preserving prose.
        if verified_citations or repaired_units:
            updated = draft
            for unit in reversed(draft_units(draft)):
                if unit['id'] in rejected:
                    replacement = ''
                elif unit['id'] in repaired_units:
                    replacement = repaired_units[unit['id']]
                elif unit['id'] in verified_citations:
                    raw = draft[unit['start']:unit['end']]
                    trailing = re.search(r'\s*$', raw)[0]
                    replacement = raw.rstrip() + f" [{verified_citations[unit['id']]}]" + trailing
                else:
                    continue
                updated = updated[:unit['start']] + replacement + updated[unit['end']:]
            updated = re.sub(r'\n[ \t]*\n(?:[ \t]*\n)+', '\n\n', updated).strip()
        logger.info('source audit completed', extra={'fields': {'removed_claims': removed, 'repaired_citations': len(repaired_units), 'valid': not issues}})
        return updated, issues, removed
    except Exception as exc:
        logger.error('source audit unavailable', extra={'fields': {'type': type(exc).__name__}})
        return draft, ['The source audit was unavailable. Verify this draft against its excerpts before using it.'], 0
