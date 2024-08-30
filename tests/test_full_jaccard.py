from copietje import normalize, tokenize, Condenser
from copietje.ranking import full_jaccard_on_token_set


def test_jaccard():
    text1 = "This is the first string."
    text2 = "This is the second string."

    condenser = Condenser(normalizer=normalize, tokenizer=tokenize)
    tokens1 = condenser.make_token_set(text1)
    tokens2 = condenser.make_token_set(text2)
    assert full_jaccard_on_token_set(tokens1, tokens2) == (4 / 6)


def test_jaccard_complete_match():
    text1 = "This is the first string."
    text2 = "This is the first string."

    condenser = Condenser(normalizer=normalize, tokenizer=tokenize)
    tokens1 = condenser.make_token_set(text1)
    tokens2 = condenser.make_token_set(text2)
    assert full_jaccard_on_token_set(tokens1, tokens2) == (5 / 5)


def test_jaccard_no_match():
    text1 = "This is the first string."
    text2 = "That was a second long."

    condenser = Condenser(normalizer=normalize, tokenizer=tokenize)
    tokens1 = condenser.make_token_set(text1)
    tokens2 = condenser.make_token_set(text2)
    assert full_jaccard_on_token_set(tokens1, tokens2) == (0 / 10)


def test_jaccard_empty_string():
    text1 = "This is the first string."
    text2 = ""

    condenser = Condenser(normalizer=normalize, tokenizer=tokenize)
    tokens1 = condenser.make_token_set(text1)
    tokens2 = condenser.make_token_set(text2)
    assert full_jaccard_on_token_set(tokens1, tokens2) == (0 / 5)


def test_jaccard_empty_strings():
    text1 = ""
    text2 = ""

    condenser = Condenser(normalizer=normalize, tokenizer=tokenize)
    tokens1 = condenser.make_token_set(text1)
    tokens2 = condenser.make_token_set(text2)
    assert full_jaccard_on_token_set(tokens1, tokens2) == 0
