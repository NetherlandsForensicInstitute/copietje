from experiments.data import read_directory, read_db


def test_read_directory(test_files):
    entries = list(read_directory(test_files))

    assert len(entries) == 2
    assert any(entry[0].name == 'data1' for entry in entries)
    assert any(entry[0].name == 'data2' for entry in entries)
    assert entries[0][1] != entries[1][1]


def test_read_db_all_data(test_database_file):
    """
    The bins in the test database contain the following counts:
    1 - 11, 2 - 13, 3 - 7, 4 - 10, 5 - 6, 6 - 6, 7 - 6, 8 - 7, 9 - 7, 10 - 2
    """
    entries = list(read_db(test_database_file, bins=None, n_versions=None))

    assert len(entries) == 75


def test_read_db_one_bin(test_database_file):
    """
    The bins in the test database contain the following counts:
    1 - 11, 2 - 13, 3 - 7, 4 - 10, 5 - 6, 6 - 6, 7 - 6, 8 - 7, 9 - 7, 10 - 2
    """
    entries = list(read_db(test_database_file, bins=[1], n_versions=None))

    assert len(entries) == 11


def test_read_db_multiple_bin(test_database_file):
    """
    The bins in the test database contain the following counts:
    1 - 11, 2 - 13, 3 - 7, 4 - 10, 5 - 6, 6 - 6, 7 - 6, 8 - 7, 9 - 7, 10 - 2
    """
    entries = list(read_db(test_database_file, bins=[1, 2, 3], n_versions=None))
    assert len(entries) == (11 + 13 + 7)

    entries = list(read_db(test_database_file, bins=[3, 6, 9, 10], n_versions=None))
    assert len(entries) == (7 + 6 + 7 + 2)


def test_read_db_single_version(test_database_file):
    """The test database contains at most 5 versions per entry. Not all entries have 5 versions."""
    entries = list(read_db(test_database_file, bins=None, n_versions=3))
    assert len(entries) == 51
