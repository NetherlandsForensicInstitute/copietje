from contextlib import contextmanager
from functools import partial
from logging import getLogger as logger
import sqlite3
import time

from datasketch import LeanMinHash
from hansken.recipes import export
from hansken.tool import run


LOG = logger(__name__)

MIN_SIZE = 16
PREFERRED_STREAMS = ('ocr', 'htmlText', 'text', 'plain')

SCHEMA = """
    CREATE TABLE IF NOT EXISTS documents (
        uid TEXT PRIMARY KEY,
        path TEXT,
        stream TEXT,
        size INTEGER,
        sha1 TEXT,
        tags TEXT,
        privileged_status TEXT,
        minhash BLOB
    )
"""


def download_documents(context):
    with sqlite3.connect('document_metadata.db') as database, context:
        database.cursor().execute(SCHEMA)
        database.row_factory = sqlite3.Row
        documents = context.search('type:document')
        with profile():
            export.bulk(documents, 'output',
                        stream=partial(determine_stream, database=database),
                        side_effect=partial(add_metadata_to_db, database=database))


def determine_stream(trace, database=None):
    # Initializing the dict with `False: MIN_SIZE` ensures that only data streams larger than the minimum size will be
    # downloaded. If there are no data streams with a size above the minimum size, this will serve as the maximum size,
    # and `False` will be returned.
    sizes = {False: MIN_SIZE}
    sizes.update({stream: trace.get(f'data.{stream}.size', 0)
                  for stream in PREFERRED_STREAMS
                  if trace.get(f'data.{stream}.mimeClass', '') == 'text'})
    return max(sizes, key=sizes.get)


def add_metadata_to_db(database, trace, stream, output, condenser=None, **_):
    mh = None

    if condenser:
        try:
            # open the freshly written file in text mode and calculate a minhash for the output
            # NB: doing this while the data is being written (as part of download.to_file in download.bulk) would be
            #     grand, but as download.bulk does not facilitate message passing and sqlite is *very* fussy about
            #     accessing things from different threads, re-reading the content here the best we have, hoping the
            #     file's contents will still be available in memory and we won't slow things down too much 🙏
            with open(output, 'rt') as text:
                mh = LeanMinHash(condenser.make_hash(text))
                buffer = bytearray(mh.bytesize('!'))
                mh.serialize(buffer, '!')
                # mh is the local used to write to the database, save the buffer to the database
                mh = buffer
        except (IOError, UnicodeError) as e:
            LOG.warning('failed to process file "%s" for trace %s', output, trace.uid, e)

    database.cursor().execute(
        """
        INSERT INTO documents (uid, path, stream, size, sha1, tags, privileged_status, minhash)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            trace.uid,
            output,
            stream,
            trace.get(f'data.{stream}.size'),
            trace.get(f'data.{stream}.hash.sha1'),
            ', '.join(trace.tags) or None,
            str(trace.privileged or '') or None,
            mh,
        )
    )


@contextmanager
def profile():
    t0 = time.perf_counter()
    yield
    print('Time:', time.perf_counter() - t0)


if __name__ == '__main__':
    run(with_context=download_documents)
