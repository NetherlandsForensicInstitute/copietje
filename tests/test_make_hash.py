import pytest

from copietje import Condenser, tokenize, normalize


def test_make_hash_simple(test_files):
    index = Condenser(tokenizer=None, normalizer=None)

    # NB: using the same input file twice (so result can only be 1.0)
    h1 = index.make_hash((test_files / 'data1').read_text('utf-8'))
    h2 = index.make_hash((test_files / 'data1').read_text('utf-8'))
    assert h1.jaccard(h2) == pytest.approx(1.0)

    h2 = index.make_hash((test_files / 'data2').read_text('utf-8'))
    assert h1.jaccard(h2) == pytest.approx(0.0)


def test_make_hash_parametrized(test_files):
    index = Condenser(tokenizer=tokenize, normalizer=normalize)
    h1 = index.make_hash((test_files / 'data1').read_text('utf-8'))
    h2 = index.make_hash((test_files / 'data2').read_text('utf-8'))

    assert h1.jaccard(h2) == pytest.approx(1.0)
