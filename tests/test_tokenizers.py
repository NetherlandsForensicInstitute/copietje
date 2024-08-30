import pytest

from copietje.tokenizers import (tokenize_split_sents,
                                 tokenize_split_words,
                                 tokenize_white_space,
                                 tokenize_white_space_n_grams,
                                 tokenize_char_n_grams)


@pytest.fixture
def example_sentence():
    return 'ABC, sing with me!'


def test_tokenize_white_space(example_sentence):
    assert list(tokenize_white_space(example_sentence)) == ['ABC,', 'sing', 'with', 'me!']


def test_tokenize_white_space_2_grams(example_sentence):
    assert list(tokenize_white_space_n_grams(example_sentence, 2)) == ['ABC, sing', 'sing with', 'with me!']


def test_tokenize_white_space_3_grams(example_sentence):
    assert list(tokenize_white_space_n_grams(example_sentence, 3)) == ['ABC, sing with', 'sing with me!']


def test_tokenize_white_space_4_grams(example_sentence):
    assert list(tokenize_white_space_n_grams(example_sentence, 4)) == ['ABC, sing with me!']


def test_tokenize_white_space_5_grams(example_sentence):
    assert list(tokenize_white_space_n_grams(example_sentence, 5)) == ['ABC, sing with me!']


def test_tokenize_split_words(example_sentence):
    assert list(tokenize_split_words(example_sentence)) == ['ABC', ',', 'sing', 'with', 'me', '!']


def test_tokenize_split_sents(example_sentence):
    assert list(tokenize_split_sents(example_sentence)) == ['ABC, sing with me!']


def test_tokenize_char_2_grams(example_sentence):
    assert list(tokenize_char_n_grams(example_sentence)) == ['AB', 'BC', 'C,', ', ', ' s', 'si', 'in', 'ng', 'g ', ' w', 'wi', 'it', 'th', 'h ', ' m', 'me', 'e!']


def test_tokenize_char_5_grams(example_sentence):
    assert list(tokenize_char_n_grams(example_sentence, n=5)) == [
        'ABC, ',
        'BC, s',
        'C, si',
        ', sin',
        ' sing',
        'sing ',
        'ing w',
        'ng wi',
        'g wit',
        ' with',
        'with ',
        'ith m',
        'th me',
        'h me!'
    ]
