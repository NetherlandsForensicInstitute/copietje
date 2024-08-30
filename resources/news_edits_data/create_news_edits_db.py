import argparse
import sqlite3
from pathlib import Path

from tqdm import tqdm


def create_article_versions_table():
    with sqlite3.connect(Path(__file__).parent / 'all_news_edits.db') as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS article_versions (
            uid TEXT PRIMARY KEY,
            original_db TEXT,
            title TEXT,
            summary TEXT,
            entry_id INT,
            num_versions INT,
            version INT,
            id INT,
            old_id INT,
            new_version INT
        )
        """)


def fill_article_versions_table(dbs_path: str):
    """
    Fills the article_versions table using the individual databases of the 'news edits article versions' dataset,
    e.g. 'ap.db', 'cbc.db'.

    - The columns title, summary, entry_id, num_versions, version, and id are copied as is.
    - The uid column is a concatenation of the database name without extension (e.g. 'ap'), the entry_id and
    version number
    (e.g. "ap_1_1.0", "cbc_23_6.0")
    - The original_db column is filled with the database name
    (e.g. "ap", "cbc")
    - From the diff table per subset we get the previous id (old_id) -- if any. This way we can track
    the sequential versions.
    (e.g. id = 32, old_id = 13 -> the version with id = 32 is derived directly from the version with id = 13)
    - The new_version column is calculated by grouping by the original_db and entry_id and ordering over versions.
    This is done since not all entries start at version 1

    A composite index is built on the original_db and entry_id columns to make the join query with data_split
    quicker.
    An index is also added for the new_version column to make filtering quicker later on

    NOTE: This takes about 25 minutes to run

    :param dbs_path: Path where all individual databases of the 'news edits article versions' dataset are
    """
    for db in tqdm(list(Path(dbs_path).glob('*.db')), desc="Writing individual databases into one database"):
        with sqlite3.connect(Path(__file__).parent / 'all_news_edits.db') as conn:
            db_name = db.stem
            attach = """
                attach ? as other_db;
                """
            append_article_versions_table = """
            INSERT INTO article_versions
                SELECT *,
                      row_number() over (PARTITION BY original_db, entry_id ORDER BY version) as new_version
                FROM (
                    SELECT ? || '_' || "entry_id" || '_' || "version" AS uid,
                          ? as original_db,
                          title,
                          summary,
                          entry_id,
                          num_versions,
                          version,
                          entryversion.id as id,
                          old_id
                    FROM other_db.diff
                        JOIN other_db.entryversion ON other_db.diff.new_id = other_db.entryversion.id
                    WHERE length(summary) > 0
                        ) tmp;
            """
            conn.execute(attach, (str(db), ))
            conn.execute(append_article_versions_table, (db_name, db_name))

    with sqlite3.connect(Path(__file__).parent / 'all_news_edits.db') as conn:
        create_index_db_entry = """
            CREATE INDEX av_original_db_entry_id_idx 
            ON article_versions (original_db, entry_id);
            """
        create_index_new_version = """
            CREATE INDEX av_new_version_idx 
            ON article_versions (new_version);
            """
        conn.execute(create_index_db_entry)
        conn.execute(create_index_new_version)


def create_data_and_fill_split_table():
    """
    Creates a 'data_split' table that contains the original_db and entry_id values from the article_versions table
    and adds a column 'ntile' which contains a number between 1 and 1000, splitting the data. Users can select a
    consistent subset by selecting one or more bins.

    A composite index is built on the original_db and entry_id columns to make the join query with article_versions
    quicker.

    NOTE: since random() doesn't have a seed in SQLite, the split changes everytime this script is ran.
    """
    with sqlite3.connect(Path(__file__).parent / 'all_news_edits.db') as conn:
        split_table_query = """
            CREATE TABLE data_split AS
                SELECT original_db, entry_id,
                        -- Shuffles the data and puts them into a 1000 numbered bins 
                       ntile(1000) over (order by random()) as ntile
                FROM article_versions
                -- group by, to get unique values
                GROUP BY original_db, entry_id;
                """

        create_index = """create index ds_original_db_entry_id_idx on data_split (original_db, entry_id);"""
        conn.execute(split_table_query)
        conn.execute(create_index)


def run(args):
    create_article_versions_table()
    fill_article_versions_table(args.path)
    create_data_and_fill_split_table()


if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    argparser.add_argument('path', type=str, help="Path to the News Edits Article Versions databases")
    args = argparser.parse_args()
    run(args)
