from pathlib import Path

import pytest


@pytest.fixture
def test_files():
    return Path(__file__).parent / 'files'


@pytest.fixture
def test_database_file():
    return Path(__file__).parent / 'database' / 'test_news_edits.db'
