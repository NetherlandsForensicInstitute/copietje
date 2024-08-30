from functools import cache, partial
from more_itertools import windowed
from typing import Iterable

import spacy


@cache
def _load_spacy(name):
    return spacy.load(name)


def tokenize_white_space(data: str) -> Iterable[str]:
    # perform a simple split on whitespace
    return data.split()


def tokenize_white_space_n_grams(data: str, n: int = 3) -> Iterable[str]:
    return [' '.join(filter(None, i)) for i in windowed(data.split(), n)]


def tokenize_split_words(data: str) -> Iterable[str]:
    nlp = _load_spacy('nl_core_news_md')
    spacied_data = nlp(data)
    return [word.text for word in spacied_data]


def tokenize_split_sents(data: str) -> Iterable[str]:
    nlp = _load_spacy('nl_core_news_md')
    spacied_data = nlp(data)
    assert spacied_data.has_annotation('SENT_START')
    return [sent.text for sent in spacied_data.sents]


def tokenize_char_n_grams(data, n=2):
    for idx in range(len(data) - n + 1):
        yield data[idx:idx + n]


TOKENIZERS = {
    'split-sents': tokenize_split_sents,
    'sents': tokenize_split_sents,
    'split-words': tokenize_split_words,
    'words': tokenize_split_words,
    'white-space': tokenize_white_space,
    'white-space-2-grams': partial(tokenize_white_space_n_grams, n=2),
    'white-space-3-grams': partial(tokenize_white_space_n_grams, n=3),
    'white-space-4-grams': partial(tokenize_white_space_n_grams, n=4),
    'white-space-5-grams': partial(tokenize_white_space_n_grams, n=5),
    'white-space-6-grams': partial(tokenize_white_space_n_grams, n=6),
    'ws': tokenize_white_space,
    '1-grams': partial(tokenize_char_n_grams, n=1),
    '2-grams': partial(tokenize_char_n_grams, n=2),
    '3-grams': partial(tokenize_char_n_grams, n=3),
    '4-grams': partial(tokenize_char_n_grams, n=4),
    '5-grams': partial(tokenize_char_n_grams, n=5),
    '6-grams': partial(tokenize_char_n_grams, n=6),
}
TOKENIZERS[''] = TOKENIZERS['ws']
