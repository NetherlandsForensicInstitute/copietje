import pytest

from copietje import Condenser, normalize, tokenize
from copietje.ranking import rank, score


@pytest.fixture
def condenser():
    return Condenser(tokenizer=tokenize, normalizer=normalize)


@pytest.fixture
def corpus(condenser):
    return {'data1': condenser.make_hash('some tokens'),
            'data2': condenser.make_hash('some more tokens')}


def test_score(corpus, condenser):
    # data1 should be identical, data2 should be lower (0.71... was observer when writing this test)
    assert list(score(corpus, condenser.make_hash('some tokens'))) == [
        (pytest.approx(1.0), 'data1'),
        (pytest.approx(0.7, rel=0.1), 'data2'),
    ]
    # order should remain unchanged, data2 should score higher
    assert list(score(corpus, condenser.make_hash('more tokens'))) == [
        (pytest.approx(0.3, rel=0.1), 'data1'),
        (pytest.approx(0.6, rel=0.1), 'data2'),
    ]


def test_rank(corpus, condenser):
    # similar to score, but the ordering should be different now
    assert [item[1] for item in rank(corpus, condenser.make_hash('some tokens'))] == ['data1', 'data2']
    assert [item[1] for item in rank(corpus, condenser.make_hash('more tokens'))] == ['data2', 'data1']


def test_filtered_rank(corpus, condenser):
    # don't care about the ordering, but the threshold should filter particular elements out
    assert {item[1] for item in rank(corpus, condenser.make_hash('some tokens'), threshold=0.1)} == {'data1', 'data2'}
    assert {item[1] for item in rank(corpus, condenser.make_hash('some tokens'), threshold=0.9)} == {'data1'}
    assert {item[1] for item in rank(corpus, condenser.make_hash('more tokens'), threshold=0.5)} == {'data2'}
