from app.rag_client import Retriever


def test_named_guest_is_reachable_even_when_not_in_initial_vector_matches():
    class Collection:
        def count(self): return 100
        def query(self, **kwargs):
            assert kwargs['where'] == {'guest': {'$in': ['Rare Guest']}}
            return {'ids': [['rare::0']], 'documents': [['Launch evidence.']],
                    'metadatas': [[{'guest': 'Rare Guest', 'title': 'Rare Guest launch'}]],
                    'distances': [[0.1]]}
    retriever = Retriever.__new__(Retriever)
    retriever.collection = Collection()
    retriever.known_guests = {'Rare Guest', 'Other Guest'}
    assert retriever.query('What did Rare Guest launch?')[0].guest == 'Rare Guest'


def test_overlapping_passages_do_not_crowd_out_distinct_evidence():
    passage = ' '.join(f'word{i}' for i in range(100))
    distinct = ' '.join(f'other{i}' for i in range(100))
    class Collection:
        def count(self):
            return 3
        def query(self, **kwargs):
            return {'ids': [['a', 'b', 'c']],
                    'documents': [[passage, 'intro ' + passage, distinct]],
                    'metadatas': [[{'episode_slug': 'episode'}] * 3],
                    'distances': [[0.1, 0.15, 0.2]]}
    retriever = Retriever.__new__(Retriever)
    retriever.collection = Collection()
    results = retriever.query('question', k=2)
    assert [c.chunk_id for c in results] == ['a', 'c']
    assert results[0].similarity > results[1].similarity


def test_uncertain_upstream_video_metadata_uses_actual_transcript():
    class Collection:
        def count(self): return 1
        def query(self, **kwargs):
            return {'ids':[['merci-grace::1']], 'documents':[['Merci Grace discusses onboarding.']],
                    'metadatas':[[{'guest':'Merci Grace','episode_slug':'merci-grace',
                                  'title':'Advice | Matt Mochary','youtube_url':'https://wrong.video',
                                  'source_path':'episodes/merci-grace/transcript.md'}]],'distances':[[0.1]]}
    retriever=Retriever.__new__(Retriever);retriever.collection=Collection()
    chunk=retriever.query('onboarding')[0]
    assert chunk.youtube_url == ''
    assert 'merci-grace/transcript.md' in chunk.deep_link
    assert 'metadata uncertain' in chunk.title


def test_distinct_episodes_are_preferred_over_more_passages_from_one_episode():
    class Collection:
        def count(self):return 3
        def query(self,**kwargs):
            return {'ids':[['first::0','first::1','second::0']],
                    'documents':[['activation evidence','different milestones','onboarding evidence']],
                    'metadatas':[[{'guest':'First'},{'guest':'First'},{'guest':'Second'}]],
                    'distances':[[0.1,0.15,0.2]]}
    retriever=Retriever.__new__(Retriever);retriever.collection=Collection()
    assert [c.chunk_id for c in retriever.query('activation',k=2)]==['first::0','second::0']


def test_same_first_name_does_not_validate_another_guests_title():
    class Collection:
        def count(self): return 1
        def query(self, **kwargs):
            return {'ids': [['matt-mullenweg::0']], 'documents': [['Open source.']],
                    'metadatas': [[{'guest': 'Matt Mullenweg', 'title': 'The one question that saves product careers | Matt LeMay',
                                   'youtube_url': 'https://wrong.video'}]], 'distances': [[0.1]]}
    retriever = Retriever.__new__(Retriever)
    retriever.collection = Collection()
    result = retriever.query('open source')[0]
    assert result.youtube_url == ''
    assert 'matt-mullenweg/transcript.md' in result.source_url
