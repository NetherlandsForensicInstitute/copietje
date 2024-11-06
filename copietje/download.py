from logging import getLogger as logger

from datasketch import LeanMinHash


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
    );
    CREATE TABLE IF NOT EXISTS errors (
        uid TEXT,
        -- equivalent to UNIXEPOCH(), which doesn't seem to be supported
        ts INTEGER DEFAULT (CAST(strftime('%s', 'now') as INTEGER)),
        stream TEXT,
        privileged_status TEXT,
        error TEXT,
        -- compound primary key to allow multiple failures of the same trace uid, differentiated by timestamp
        PRIMARY KEY (uid, ts)
    );
"""


def determine_stream(trace, database=None):
    # Initializing the dict with `False: MIN_SIZE` ensures that only data streams larger than the minimum size will be
    # downloaded. If there are no data streams with a size above the minimum size, this will serve as the maximum size,
    # and `False` will be returned.
    sizes = {False: MIN_SIZE}
    sizes.update({stream: trace.get(f'data.{stream}.size', 0)
                  for stream in PREFERRED_STREAMS
                  if trace.get(f'data.{stream}.mimeClass', '') == 'text'})
    selected = max(sizes, key=sizes.get)

    if selected and database:
        cursor = database.cursor()
        # a stream has been selected, and we've been handed a database, attempt to select trace' stream sha1
        cursor.execute(
            """
            SELECT sha1 FROM documents WHERE uid = ?
            """,
            (trace.uid,)
        )
        # if the query had a result, skip this trace if the stored digest matches the one in trace' metadata
        if (row := cursor.fetchone()) and row['sha1'] == trace.get(f'data.{selected}.hash.sha1'):
            LOG.debug('skipping download for trace %s, already present in database (sha1=%s)', trace.uid, row['sha1'])
            return False

    LOG.debug('selected stream %s to download for trace %s', selected, trace.uid)
    return selected


def log_error_to_db(database, trace, stream, exception=None, **_):
    database.cursor().execute(
        """
        INSERT INTO errors (uid, stream, privileged_status, error)
        VALUES (?, ?, ?, ?)
        """,
        (
            trace.uid,
            stream,
            str(trace.privileged or '') or None,
            str(exception) if exception else None,
        )
    )
    database.commit()


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
    # commit open transactions now, a crashing download would otherwise roll back any open inserts
    database.commit()
