import pytest

from copietje import Condenser, HASH_FUNCTIONS
from copietje.normalizers import NORMALIZERS
from copietje.tokenizers import TOKENIZERS


def test_broken():
    with pytest.raises(AttributeError):
        Condenser.from_spec(None)
    with pytest.raises(ValueError):
        Condenser.from_spec('')
    with pytest.raises(KeyError):
        Condenser.from_spec('ws::md5:')
    with pytest.raises(ValueError):
        Condenser.from_spec('ws:::forty_two')


def test_minimal():
    condenser = Condenser.from_spec(':::')

    assert condenser.tokenizer is TOKENIZERS['ws']
    assert condenser.normalizer is NORMALIZERS['norm-html']
    assert condenser.hash_func is HASH_FUNCTIONS['sha1']
    assert condenser.permutations is 128


@pytest.mark.parametrize(
    ('spec', 'tok', 'norm', 'hf', 'perms'),
    (
        (':::', TOKENIZERS['ws'], NORMALIZERS['norm-html'], HASH_FUNCTIONS['sha1'], 128),
        ('6-grams:norm::256', TOKENIZERS['6-grams'], NORMALIZERS['norm'], HASH_FUNCTIONS['sha1'], 256),
        ('words::mmh3:', TOKENIZERS['words'], NORMALIZERS['norm-html'], HASH_FUNCTIONS['mmh3'], 128),
    ),
)
def test_from_spec(spec, tok, norm, hf, perms):
    condenser = Condenser.from_spec(spec)

    assert condenser.tokenizer is tok
    assert condenser.normalizer is norm
    assert condenser.hash_func is hf
    assert condenser.permutations is perms
