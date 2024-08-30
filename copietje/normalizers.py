from cleantext import clean
from bs4 import BeautifulSoup


def normalize(data: str) -> str:
    """
    Uses the clean function from clean-text package. See the documentation for all options:
    https://github.com/jfilter/clean-text
    """
    return clean(data,
                 fix_unicode=True,  # fix various unicode errors
                 to_ascii=True,  # transliterate to closest ASCII representation
                 lower=True,  # lowercase text
                 no_line_breaks=True,  # fully strip line breaks as opposed to only normalizing them
                 no_currency_symbols=True,  # replace all currency symbols with a special token
                 replace_with_currency_symbol='',
                 no_punct=True  # remove punctuations
                 )


def normalize_html(data: str):
    """
    Removed html text such as <br>, <p>, then calls the normalize() function
    """
    soup = BeautifulSoup(data, features='html.parser')
    return normalize(soup.get_text())


NORMALIZERS = {
    'norm': normalize,
    'norm-html': normalize_html,
}
NORMALIZERS[''] = NORMALIZERS['norm-html']
