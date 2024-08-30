import sqlite3

from pathlib import Path
from os import walk
from typing import Sequence, List


def read_directory(path):
    for root, _, files in walk(path):
        for file in files:
            p = Path(root, file)
            with p.open('r') as data:
                yield p, data.read()


def read_db(path: str | Path, bins: Sequence[int] = None, n_versions: int | None = 2):
    """
    Read (part of) the data from the article_versions and data_split table.

    About the bins parameter:
    To select a subset of the data, bin numbers are added to the data in the 'ntile' column. The data is split into
    1000 bins, thus the numbers 1-1000 can be chosen. NOTE: the bins are not necessarily equisized, since the
    data is first grouped by the original_db and the entry_id. This was done to ensure that all versions of a single
    entry will all be in the same bin.
    The bins can be used to test for different scenarios, e.g. test a big amount of data for speed, test a small
    amount to see if the code runs, get a set you've never seen before, etc. This is more or less a freeform way of
    selecting train/test/eval splits. e.g. to test on a smaller set, bins can be set to [1] (or [8] or [4] or ...,
    the actual number doesn't matter), then about 1000 results are returned. To test on a bigger set, e.g. 60%,
    bins can be set to list(range(1, 600)). If you then want new data to evaluate, bins can
    be set to list(range(700,1001))

    About the n_versions:
    In the data we see that some texts are completely changed at some point, by limiting the number of versions to
    select, we have a bigger chance of only having minor changes between versions of the same entry

    :param path: Path to sqlite database file
    :param bins: list of bin numbers ( possible values [1...1000] ) to select a subset of the data. If set to None,
    then all bins are returned
    :param n_versions: Number of versions per entry to select. If set to None, then all versions are returned
    :yield: uid, summary
    """
    where = []
    params: List = []
    if bins is not None:
        if not all([isinstance(n, int) for n in bins]):
            raise ValueError(f"List of bins should only contain integers, got types '{[type(n) for n in bins]}'")
        if not all([1 <= n <= 1000 for n in bins]):
            raise ValueError(f"List of bins should only contain integers between 1 and 10, got numbers '{bins}'")

        if len(bins) == 1:
            where.append('ntile = ?')
        else:
            where.append(f"ntile IN ({', '.join(['?'] * len(bins))})")
        params += bins

    if n_versions is not None:
        if not isinstance(n_versions, int):
            raise ValueError(f"n_versions should be an integer, got type '{type(n_versions)}'")
        where.append('new_version <= ?')
        params.append(n_versions)

    with sqlite3.connect(path) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        sql = """
            SELECT av.*
            FROM data_split AS ds
            JOIN article_versions AS av ON av.original_db = ds.original_db AND av.entry_id = ds.entry_id
            """
        if where:
            sql += 'WHERE '
            sql += ' AND '.join(where)
            cur.execute(sql, params)
        else:
            cur.execute(sql)
        for row in cur:
            yield row['uid'], row['summary']
