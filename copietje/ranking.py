from os import PathLike
from typing import Tuple, Iterable

from copietje import Condenser


def rank(corpus, query_hash, threshold=None):
    return sorted(
        score(corpus, query_hash, threshold=threshold),
        # sort the most similar on top (1.0 → 0.0)
        reverse=True,
    )


def score(corpus, query_hash, threshold=None):
    # use provided threshold or value that functions as 'no threshold'
    threshold = threshold or 0.0
    return (
        # create 2-tuples of (similarity, document) for every document in the corpus
        (similarity, identifier)
        for identifier, doc_hash in corpus.items()
        # calculate similarity, immediately use that as a filter
        if (similarity := query_hash.jaccard(doc_hash)) >= threshold
    )


def rank_matrix(corpus):
    for query_path, query_hash in corpus.items():
        yield query_path, rank(corpus, query_hash)


def score_matrix(corpus):
    for query_path, query_hash in corpus.items():
        yield query_path, score(corpus, query_hash)


def corpus_from_generator(iter_data: Iterable[Tuple[PathLike, str]], condenser=None):
    condenser = condenser or Condenser()
    return {path: condenser.make_hash(data)
            for path, data in iter_data}


def full_jaccard_on_token_set(tokens1: set, tokens2: set):
    union_length = len(tokens1 | tokens2)
    # Check if union is 0 to avoid division by 0 errors.
    # Union will be 0 if both strings are empty (or only contain white space).
    if union_length == 0:
        return 0

    return len(tokens1 & tokens2) / union_length


def full_jaccard(corpus, query_token_set):
    return (
        # create 2-tuples of (jaccard, document) for every document in the corpus
        (full_jaccard_on_token_set(query_token_set, token_set), identifier)
        for identifier, token_set in corpus.items()
    )


def full_jaccard_matrix(corpus):
    for query_path, query_token_set in corpus.items():
        yield query_path, full_jaccard(corpus, query_token_set)


def full_token_set_from_generator(iter_data: Iterable[Tuple[str, str]], condenser=None):
    condenser = condenser or Condenser()
    return {path: condenser.make_token_set(data)
            for path, data in iter_data}
