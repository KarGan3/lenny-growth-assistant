import pytest
from app.evidence_audit import apply_audit, draft_units


@pytest.mark.parametrize('claim,supported', [
    ('She compared 30-day conversion rates and retention rates.', False),
    ('She compared 90-day conversion rates and 30-day retention rates.', True),
    ('Hila Qu identified the first PR as a valuable action.', False),
    ('Hila Qu identified activation improvements.', True),
])
def test_literal_details_preserve_corrected_numbers_and_actual_cited_actions(claim, supported):
    from app.evidence_audit import explicit_details_supported
    passage = 'Hila Qu: What is the 30 day conversion rate? Not 30 day, 90 day conversion rate. What is the 30 day retention rate? We improved activation with guided onboarding.'
    assert explicit_details_supported(passage, claim) is supported


def test_standard_expanded_acronym_is_not_rejected():
    from app.evidence_audit import explicit_details_supported
    assert explicit_details_supported('Users merge their first pull request.', 'Users merge their first PR.')
    assert explicit_details_supported('Users merge their first pull request.', 'Users merge something like PR.')


@pytest.mark.parametrize('company,supported', [('Gojek', True), ('Gojaja', False)])
def test_named_organization_must_exist_in_the_cited_passage(company, supported):
    from app.evidence_audit import explicit_details_supported
    assert explicit_details_supported('Crystal described her work at Gojek.', f'Crystal described growth gaps at {company}.') is supported


@pytest.mark.parametrize('passage,claim,supported', [
    ('Email surveys establish a new baseline.', 'Forty percent were disappointed.', False),
    ('40.0% were disappointed.', 'Forty percent were disappointed.', True),
    ('30-day retention was measured.', '90-day conversion was measured.', False),
    ('Three month retention was measured.', '3-month retention was measured.', True),
    ('30 day conversion. Not 30 day, 90 day conversion.', 'Thirty-day conversion was measured.', False),
])
def test_figures_and_measurement_windows_need_the_actual_cited_passage(passage, claim, supported):
    from app.evidence_audit import explicit_details_supported
    assert explicit_details_supported(passage, claim) is supported


def test_citation_repair_cannot_invent_support_for_an_absent_figure(monkeypatch):
    from app import evidence_audit
    from app.config import Settings
    from app.llm.factory import RoutedLLMClient
    class Verifier:
        def score(self, evidence, claim): return 1.0
    monkeypatch.setattr(evidence_audit, 'get_verifier', lambda path: Verifier())
    updated, issues, removed = evidence_audit.audit_evidence(RoutedLLMClient(Settings()),
        '70% were disappointed. [2]', {1: '40% were disappointed.', 2: 'Email surveys.'})
    assert updated == '' and not issues and removed == 1


def test_reviewer_can_remove_an_unsupported_outcome_but_cannot_add_facts():
    draft = 'Gojek filled onboarding gaps [1]. This doubled engagement [1].'
    updated, issues, removed = apply_audit(draft, '{"unsupported_ids": [1]}')
    assert updated == 'Gojek filled onboarding gaps [1].'
    assert not issues and removed == 1


@pytest.mark.parametrize('response', [
    'I think it looks good.',
    '{"unsupported_ids": "none"}',
    '{"unsupported_ids": [99]}',
])
def test_unreliable_review_cannot_silently_certify_or_replace_a_draft(response):
    draft = 'An attributed source example [1].'
    updated, issues, removed = apply_audit(draft, response)
    assert updated == draft
    assert issues and removed == 0


def test_audit_accepts_wrapped_sentences_and_fenced_json():
    updated, issues, removed = apply_audit('Supported [1].\nUnreported causal\noutcome [1].',
        '```json\n{"unsupported_ids": [1]}\n```')
    assert updated == 'Supported [1].'
    assert not issues and removed == 1


def test_reviewer_cannot_remove_negation_or_other_sentence_fragments():
    draft = 'The speaker did not report an improvement [1].'
    updated, issues, removed = apply_audit(draft, '{"unsupported_ids": ["not"]}')
    assert updated == draft
    assert issues and removed == 0


def test_units_keep_negation_and_citations_inside_a_whole_sentence():
    units = draft_units('# Findings\n\nThe speaker did not report an improvement. [1] A different example follows [2].\n\n* Suggested action\n* Another action')
    assert [u['text'] for u in units] == ['# Findings', 'The speaker did not report an improvement. [1]', 'A different example follows [2].', '* Suggested action', '* Another action']


def test_verified_fact_gets_corrected_reference_without_changing_its_prose(monkeypatch):
    from app import evidence_audit
    from app.config import Settings
    from app.llm.factory import RoutedLLMClient
    class Verifier:
        def score(self, evidence, claim): return 1.0 if evidence == 'correct source' else 0.0
    monkeypatch.setattr(evidence_audit, 'get_verifier', lambda path: Verifier())
    updated, issues, removed = evidence_audit.audit_evidence(RoutedLLMClient(Settings()),
        'Gojek filled onboarding gaps [2].', {1: 'correct source', 2: 'unrelated source'})
    assert updated == 'Gojek filled onboarding gaps. [1]'
    assert not issues and removed == 0
    updated, issues, removed = evidence_audit.audit_evidence(RoutedLLMClient(Settings()),
        'A supported finding [1]. Gojek filled onboarding gaps [2]. Another finding [1].',
        {1: 'correct source', 2: 'unrelated source'})
    assert updated == 'A supported finding [1]. Gojek filled onboarding gaps. [1] Another finding [1].'
    assert not issues and removed == 0


def test_missing_classifier_flags_a_draft_instead_of_certifying_it(monkeypatch):
    from app import evidence_audit
    from app.config import Settings
    from app.llm.factory import RoutedLLMClient
    def missing(path): raise FileNotFoundError('missing local weights')
    monkeypatch.setattr(evidence_audit, 'get_verifier', missing)
    draft = 'A source example [1].'
    updated, issues, removed = evidence_audit.audit_evidence(RoutedLLMClient(Settings()), draft, {1: 'evidence'})
    assert updated == draft
    assert issues and removed == 0


@pytest.mark.parametrize('draft,evidence', [
    ('Crystal Widjaja emphasizes daily retention [3].', {3: 'Albert Cheng (00:30:32): Daily retention compounds.'}),
    ('Inactive teams contribute to security [2].', {2: 'Ben Williams (01:19:28): Teams fix vulnerabilities off-platform.'}),
])
def test_speaker_and_scope_checks_do_not_trust_an_insensitive_classifier(monkeypatch, draft, evidence):
    from app import evidence_audit
    from app.config import Settings
    from app.llm.factory import RoutedLLMClient
    class Verifier:
        def score(self, evidence, claim): return 1.0
    monkeypatch.setattr(evidence_audit, 'get_verifier', lambda path: Verifier())
    updated, issues, removed = evidence_audit.audit_evidence(RoutedLLMClient(Settings()), draft, evidence)
    assert updated == ''
    assert not issues and removed == 1


def test_a_named_claim_is_checked_against_that_speakers_turns_not_the_interviewers(monkeypatch):
    from app import evidence_audit
    from app.config import Settings
    from app.llm.factory import RoutedLLMClient
    checked = []
    class Verifier:
        def score(self, evidence, claim):
            checked.append(evidence)
            return 1.0 if 'motivations' in evidence else 0.0
    monkeypatch.setattr(evidence_audit, 'get_verifier', lambda path: Verifier())
    draft = 'According to Merci Grace, users have different motivations [5].'
    evidence = {5: 'Lenny (26:12): Users have different motivations.\nMerci Grace (26:49): Design from the first introduction.'}
    updated, issues, removed = evidence_audit.audit_evidence(RoutedLLMClient(Settings()), draft, evidence)
    assert updated == '' and not issues and removed == 1
    assert checked and all('Lenny' not in text and 'Merci Grace' in text for text in checked)


def test_pruning_keeps_a_verified_citation_on_surviving_facts(monkeypatch):
    from app import evidence_audit
    from app.config import Settings
    from app.llm.factory import RoutedLLMClient
    class Verifier:
        def score(self, evidence, claim): return 1.0 if evidence == 'supporting passage' else 0.0
    monkeypatch.setattr(evidence_audit, 'get_verifier', lambda path: Verifier())
    updated, issues, removed = evidence_audit.audit_evidence(RoutedLLMClient(Settings()),
        'The team fixes vulnerabilities.', {1: 'other passage', 2: 'supporting passage'})
    assert updated == 'The team fixes vulnerabilities. [2]'
    assert not issues and removed == 0


@pytest.mark.parametrize('turn,expected_removed', [
    ('Our onboarding investments included guided onboarding and education.', 1),
    ('The activation metric is defined as a team collaborating in week four.', 0),
])
def test_metric_definition_needs_measurement_evidence_not_only_related_tactics(monkeypatch, turn, expected_removed):
    from app import evidence_audit
    from app.config import Settings
    from app.llm.factory import RoutedLLMClient
    class Verifier:
        def score(self, evidence, claim): return 1.0
    monkeypatch.setattr(evidence_audit, 'get_verifier', lambda path: Verifier())
    evidence = {1: 'Episode metadata: Lauryn Isford — Onboarding\nLenny (00:15:36): What metric did you define?\nLauryn Isford (00:15:38): '+turn}
    _, issues, removed = evidence_audit.audit_evidence(RoutedLLMClient(Settings()),
        'The activation metric is defined by collaboration in week four. [1]', evidence)
    assert not issues and removed == expected_removed
