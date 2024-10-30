import argparse
from functools import partial
from inspect import signature, Parameter
import logging
from pathlib import Path
import sqlite3
from zoneinfo import ZoneInfo

from datasketch import LeanMinHash, MinHashLSH
from hansken.query import Term
from hansken.recipes import export
from hansken.tool import create_argument_parser, resolve_logging, run

from copietje import Condenser
from copietje.download import add_metadata_to_db, determine_stream, SCHEMA
from copietje.ranking import rank


LOG = logging.getLogger(__name__)
LOG.addHandler(logging.NullHandler())


def zero_to_one(value):
    if not 0.0 <= (value := float(value)) <= 1.0:
        raise TypeError('should be [0.0-1.0]')
    return value


download_parser = create_argument_parser(requires_project=True, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
download_parser.add_argument('database', metavar='DATABASE', help='path to database file')
download_parser.add_argument('--target', help='path to download root, defaults to directory that contains '
                                              'the database')
download_parser.add_argument('--limit', type=int, default=None, help='max number of traces to download')
download_parser.add_argument('--condenser', type=Condenser.from_spec, default=Condenser(),
                             help='tokenizer, normalizer, hash algorithm and permutations to be used for minhashing, '
                                  'separated by : (e.g.: "ws:norm-html:sha1:128")')
num_jobs = download_parser.add_mutually_exclusive_group(required=False)
num_jobs.add_argument('--jobs', dest='jobs', type=int, default=4,
                      help='number of parallel tasks during download')
num_jobs.add_argument('--no-parallel', dest='jobs', action='store_false',
                      help='turn of parallelism during download')

match_parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
match_parser.add_argument('-l', '--log', metavar='FILE', default=None,
                          help='log messages to FILE (use - for standard error, log messages are hidden by default)')
match_parser.add_argument('-v', '--verbose', action='count', default=0, help='be verbose')
match_parser.add_argument('-z', '--timezone', type=ZoneInfo, default=ZoneInfo('Europe/Amsterdam'),
                          help=argparse.SUPPRESS)
match_parser.add_argument('database', metavar='DATABASE', help='path to database file')
match_parser.add_argument('--threshold', type=zero_to_one, default=0.5,
                          help='minimum value that considers documents similar')
match_parser.add_argument('--false-negative-weight', dest='fn_weight', type=zero_to_one, default=0.75,
                          help='relative weight of false negative results to optimize minhash index for')


def main():
    # before handing argument parsing off to hansken.py or our own command line parser, pop the subcommand off of the
    # arguments here
    import sys
    args = sys.argv[1:]
    subcommand = args.pop(0) if args else None

    match subcommand:
        case 'download':
            # use hansken.py's entrypoint with an unwrapped download function as the callback
            return run(args, with_context=partial(_unwrap, target_func=download), using_parser=download_parser)
        case 'match':
            # turn remaining command line arguments into an argparse namespace
            args = match_parser.parse_args(args)
            with resolve_logging(args):
                # unwrap the argparse namespace into keyword arguments and call the function to do the thing
                return _unwrap(match, args=args)
        case '-h':
            return usage()
        case '--help':
            return usage()
        case _:
            # anything else: print usage, combined with a non-zero exit code
            return usage(2)


def usage(exitcode=0):
    # mimic the output of argparse
    print('usage: copietje [-h] [download | match]')
    print('copietje: error: choose from subcommands download, match')
    raise SystemExit(exitcode)


def download(*, context, database, target=None, limit=None, condenser=None, jobs=4):
    if not target:
        # default target to be the folder where the database is stored
        target = Path(database).parent
        LOG.info('using download target derived from database: %s')
    # make sure the target directory exists
    target.mkdir(parents=True, exist_ok=True)

    with context, sqlite3.connect(database) as database:
        database.row_factory = sqlite3.Row
        database.cursor().execute(SCHEMA)
        # search hansken for the documents to download + minhash
        documents = context.search(Term('type', 'document'), count=limit)
        # issue bulk download with side effects to store all the documents and the minhashes
        LOG.info('starting bulk download of %d results (limited to %d)', documents.num_results, limit)
        export.bulk(documents, target,
                    stream=partial(determine_stream, database=database),
                    side_effect=partial(add_metadata_to_db, database=database, condenser=condenser),
                    jobs=jobs)


def match(*, database, threshold=0.5, fn_weight=0.75):
    with sqlite3.connect(database) as database:
        database.row_factory = sqlite3.Row
        permutations = _get_permutations(database)
        # build index of documents that already have a label
        index = MinHashLSH(threshold=threshold, weights=(1.0 - fn_weight, fn_weight), num_perm=permutations)
        # also track the labeled uids with their minhashes to post-process results later
        hashes = {}
        labeled = database.cursor().execute("""
            SELECT uid, minhash FROM documents
            WHERE privileged_status IS NOT NULL AND minhash IS NOT NULL
        """)
        LOG.info('building index of labeled documents...')
        for document in labeled:
            mh = LeanMinHash.deserialize(document['minhash'], '!')
            index.insert(key=document['uid'],
                         minhash=mh,
                         # avoid duplicate keys check, the uid column will be unique
                         check_duplication=False)
            hashes[document['uid']] = mh
        LOG.info('indexed %d documents', len(hashes))

        documents = database.cursor().execute("""
            SELECT uid, minhash FROM documents
            WHERE privileged_status IS NULL AND minhash IS NOT NULL
        """)
        LOG.info('matching unlabeled documents to index...')
        num_documents = num_matches = 0
        # match all *other* documents to previously created index
        for num_documents, document in enumerate(documents, start=1):
            query_hash = LeanMinHash.deserialize(document['minhash'], '!')
            # collect not only the uids but also their corresponding minhashes to post-process the results
            matches = {uid: hashes[uid] for uid in index.query(query_hash)}
            # filter + rank matches, only output if filter leaves anything
            if matches := rank(matches, query_hash, threshold=threshold):
                print(document['uid'], f' # max {matches[0][0]:.3f} matches', ', '.join(match[1] for match in matches))
                num_matches += 1

        LOG.info('matched %d out of %d documents', num_matches, num_documents)


def _get_permutations(database):
    cursor = database.cursor().execute("""
        SELECT minhash FROM documents WHERE minhash IS NOT NULL LIMIT 1
    """)
    minhash = LeanMinHash.deserialize(cursor.fetchone()['minhash'], '!')
    return len(minhash.hashvalues)


def _unwrap(target_func, *, context=None, args):
    # TODO: this translation between hansken.py's handling of argparse additions and the callback should really be
    #       handled by hansken.py itself

    # collect arguments that target_func will need, starting with the context that hansken.py created for us
    kwargs = {'context': context} if context else {}
    for name, param in signature(target_func).parameters.items():
        # we're looping the expected arguments, context is an argument that we should *not* take from args, (…)
        if not kwargs.get(name):
            # (…) otherwise: retrieve the defined arguments from args, defaulting to the function's default in case
            # it's not provided by args
            if (value := getattr(args, name, param.default)) is Parameter.empty:
                # no value for name, only possible when it has no default in the function definition and also not
                # specified through argparse (conclusion: we can't call the function)
                raise TypeError(f'no value for argument {name}')

            kwargs[name] = value

    # call the target function with all collected arguments
    return target_func(**kwargs)


if __name__ == '__main__':
    main()
