from datetime import datetime
from functools import partial
from pathlib import Path
import time

import confidence

from copietje import Condenser, normalize
from experiments.data import read_db
from copietje.ranking import corpus_from_generator
from copietje.tokenizers import (tokenize_split_sents,
                                 tokenize_split_words,
                                 tokenize_white_space,
                                 tokenize_char_n_grams)


here = Path(__file__).parent
paths = confidence.load_name('copietje')

run_timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
tokenizers = {
    'split_sents': tokenize_split_sents,
    'split_words': tokenize_split_words,
    'white_space': tokenize_white_space,
    '1-grams': partial(tokenize_char_n_grams, n=1),
    '2-grams': partial(tokenize_char_n_grams, n=2),
    '3-grams': partial(tokenize_char_n_grams, n=3),
    '4-grams': partial(tokenize_char_n_grams, n=4),
    '5-grams': partial(tokenize_char_n_grams, n=5),
    '6-grams': partial(tokenize_char_n_grams, n=6),
}



# test all tokenizers
for experiment_name, tokenizer in tokenizers.items():
    hasher = Condenser(tokenizer=tokenizer,
                       normalizer=normalize)
    start_time = time.perf_counter()
    corpus = corpus_from_generator(read_db(paths['news-edit-db-path'], bins=[1], n_versions=2), hasher)
    run_time = time.perf_counter() - start_time
    print(f'{tokenizer} loaded in {round(run_time, 2)} seconds')
    with open(here / f"output/{run_timestamp}-timer-experiment.txt", 'a') as f:
        f.writelines((
            # a header with the name of the tokenizer
            experiment_name, '\n',
            str(run_time), '\n'))