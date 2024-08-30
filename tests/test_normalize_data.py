from copietje import normalize, normalize_html


def test_normalize():
    data = """
        Some $TEXT

        wIth       CAPITALS !

        - SpAces, CharacTers& and punctuation?
    """
    normalized_data = normalize(data)

    assert normalized_data == "some text with capitals spaces characters and punctuation"


def test_normalize_html():
    data = """
            <p>Some $TEXT</p><br>

            wIth       <h1>CAPITALS !</h1>

            - SpAces, CharacTers& and punctuation?
        """
    normalized_data = normalize_html(data)

    assert normalized_data == "some text with capitals spaces characters and punctuation"
