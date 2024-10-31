from operator import itemgetter
import sqlite3
from sqlite3 import Connection
from typing import Callable, Iterable, Set, Tuple
from zipfile import ZipFile
from zlib import crc32

from datasketch import MinHash, MinHashLSH, LeanMinHash
from datasketch.hashfunc import sha1_hash32
from mmh3 import hash as mmh3_hash

from copietje.normalizers import normalize_html, NORMALIZERS
from copietje.tokenizers import tokenize_white_space, TOKENIZERS


# the module default is the simple white space tokenizer
tokenize = tokenize_white_space
# the module default is normalize_html, which removes html code and then runs the basic normalizer
normalize = normalize_html


def mmh3_unsigned(data):
    return mmh3_hash(data, signed=False)


HASH_FUNCTIONS = {
    'sha1': sha1_hash32,
    'mmh3': mmh3_unsigned,
    'crc32': crc32,
}
HASH_FUNCTIONS[''] = HASH_FUNCTIONS['sha1']

DEFAULT_PERMUTATIONS = 128


class Condenser:
    @classmethod
    def from_spec(cls, spec):
        """
        Create a condenser from a simplified string, formatted as
        ``'tokenizer:normalizer:hash_function:number_of_permutations'``
        (e.g. ``'ws:norm:'`` to use white space tokenizer, simple
        normalizer, the default hash function (empty string) and the
        default number of permutations). See global dicts for
        available values.
        """
        t, n, h, p = spec.split(':')
        return cls(TOKENIZERS[t], NORMALIZERS[n], HASH_FUNCTIONS[h], int(p) if p else DEFAULT_PERMUTATIONS)

    def __init__(self,
                 tokenizer: Callable[[str], Iterable[str]] | None = tokenize,
                 normalizer: Callable[[str], str] | None = normalize,
                 hash_function: Callable = sha1_hash32,
                 permutations: int = DEFAULT_PERMUTATIONS):
        # use provided tokenizer, or non-tokenizing fallback
        self.tokenizer = tokenizer or self._single_token
        self.normalizer = normalizer
        self.hash_func = hash_function
        self.permutations = permutations

    def _single_token(self, data):
        yield data

    def make_hash(self, data: str) -> MinHash:
        mh = MinHash(hashfunc=self.hash_func, num_perm=self.permutations)

        if self.normalizer:
            data = self.normalizer(data)

        mh.update_batch((
            # encode every token, mh expects bytes
            token.encode('utf-8') for token in self.tokenizer(data)
        ))

        return mh

    def make_token_set(self, data: str) -> Set[str]:
        if self.normalizer:
            data = self.normalizer(data)

        return set(self.tokenizer(data))


class HashIndex:
    def __init__(self,
                 condenser: Condenser,
                 database: Connection,
                 index: MinHashLSH = None):
        self.condenser = condenser
        self.database = database
        self.database.row_factory = sqlite3.Row
        self.index = index or MinHashLSH(threshold=.8)

    def make_index(self, zip_file: str):
        with ZipFile(zip_file) as documents_zip:
            cur = self.database.cursor()

            cur.execute("""
                SELECT path, uid, stream, minhash
                FROM documents
                WHERE tags IS NOT NULL
            """)
            for row in cur:
                if minhash := self._get_or_update_minhash(row, documents_zip):
                    self.index.insert(row['uid'], minhash)

    def query_index(self, zip_file: str) -> Iterable[Tuple[str, Iterable[Tuple[str, float]]]]:
        with ZipFile(zip_file) as documents_zip:
            cur = self.database.cursor()

            cur.execute("""
                SELECT path, uid, stream, minhash
                FROM documents
                WHERE tags IS NULL
            """)
            for row in cur:
                if query_hash := self._get_or_update_minhash(row, documents_zip):
                    if matches := self.index.query(query_hash):
                        # build matches as a list of 2-tuples (uid, similarity)
                        matches = [(match_uid, query_hash.jaccard(self.get_minhash(match_uid)))
                                   for match_uid in matches]
                        # provide the uid that hit the database and a ranked list of (uid, similarity)
                        yield row['uid'], sorted(matches, key=itemgetter(1), reverse=True)

    def query_index_for_document(self, document: str, key: str = None):
        min_hash = self.condenser.make_hash(document)
        print(key, 'alike', self.index.query(min_hash))

    def get_minhash(self, uid: str) -> MinHash:
        cur = self.database.cursor()

        cur.execute("""
            SELECT minhash
            FROM documents
            WHERE uid=?
        """, (uid,))

        if len(rows := cur.fetchall()) != 1:
            raise KeyError(f'Each uid should be unique and present in the database, '
                           f'but found {len(rows)} rows for uid {uid}.')

        return LeanMinHash.deserialize(rows[0]['minhash'], '!')

    def _get_or_update_minhash(self, row, documents_zip):
        if row['minhash']:
            return LeanMinHash.deserialize(row['minhash'], '!')

        document = documents_zip.read(row['path'])
        try:
            minhash = self.condenser.make_hash(str(document, encoding='utf-8'))

            lean_minhash = LeanMinHash(minhash)
            byte_array = bytearray(lean_minhash.bytesize())
            lean_minhash.serialize(byte_array, '!')

            update_cursor = self.database.cursor()
            update_cursor.execute(
                'UPDATE documents SET minhash=? WHERE uid=?',
                (byte_array, row['uid'])
            )

            return minhash
        except UnicodeDecodeError:
            print('UnicodeDecoderError for', row['path'])
            return None


def matches_to_file(index: HashIndex, documents: str, out_file):
    with open(out_file, 'w') as out_file:
        for uid, matches in index.query_index(documents):
            out_file.write(uid)
            out_file.write('  # similar to ')
            out_file.write(', '.join(match[0] for match in matches))
            out_file.write('\n')
