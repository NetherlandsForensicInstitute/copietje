from copietje import tokenize


def test_tokenize():
    # NB: tokenization currently only applies splitting, no normalization of capital letters or punctuation is applied
    assert list(tokenize('a piece of text')) == ['a', 'piece', 'of', 'text']
    assert list(tokenize('A piece, of \r\ntext')) == ['A', 'piece,', 'of', 'text']
    assert list(tokenize('A piece , of    text')) == ['A', 'piece', ',', 'of', 'text']
