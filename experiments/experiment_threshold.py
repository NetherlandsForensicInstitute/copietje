import os
from datetime import datetime
from pathlib import Path

import confidence
import matplotlib.pyplot as plt
from numpy import arange
from tqdm import tqdm

from copietje import Condenser, normalize
from copietje.ranking import rank_matrix, corpus_from_generator
from copietje.tokenizers import TOKENIZERS
from experiments.data import read_db
from experiments.evaluation import get_id_from_uid

here = Path(__file__).parent
paths = confidence.load_name('copietje')
(here / 'output').mkdir(parents=True, exist_ok=True)

run_timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

permutation_counts=[64, 128, 256, 512]

for permutations in permutation_counts:
    done = set()
    for tokenizer_name, tokenizer in TOKENIZERS.items():
        # TOKENIZERS contains duplicates for convenience, that is inconvenient for this experiment, so track the
        # tokenizers we've already used
        if tokenizer in done:
            continue
        done.add(tokenizer)

        print(f'tokenizer: {tokenizer_name}, #perms: {permutations}')

        hasher = Condenser(tokenizer=tokenizer,
                           normalizer=normalize,
                           permutations=permutations)
        print('load corpus')
        print(os.getcwd())
        corpus = corpus_from_generator(read_db(paths["HAND_PICKED_DATA"], n_versions=2), hasher)
        print('rank matrix')
        matrix = rank_matrix(corpus)
        y_values_dup = []
        y_values_not_dup = []

        print('get scores and sort')
        # get list of scores and list of y_true
        for document, scores in tqdm(matrix):
            file_id = get_id_from_uid(document)
            #scores = sorted(scores, reverse=True)
            y_true = [int(file_id == get_id_from_uid(sim_name)) for _, sim_name in scores if document != sim_name]
            y_values = [score for score, sim_name in scores if document != sim_name]

            # separate scores based on the ground truth, so we can plot them separately
            for index, y in enumerate(y_true):
                if y == 1:
                    y_values_dup.append(y_values[index])
                else:
                    y_values_not_dup.append(y_values[index])

        print('make plot')
        plt.hist(y_values_not_dup, bins=[i for i in arange(0, 1, 1/permutations)], alpha=0.5, label='different files')
        plt.hist(y_values_dup, bins=[i for i in arange(0, 1, 1/permutations)], alpha=0.5, label='duplicates')
        plt.yscale('log')
        output_name = here / f"output/{run_timestamp}-threshold-experiment-{permutations}-perms-{tokenizer_name}.png"
        plt.title(f"t:{tokenizer_name} / p:{permutations}")
        plt.savefig(output_name)
        # clear figure
        plt.clf()
