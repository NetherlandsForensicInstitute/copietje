import csv
from datetime import datetime
from pathlib import Path

import confidence
from datasketch import MinHashLSH
from more_itertools import numeric_range

from copietje import Condenser, normalize_html, tokenize, HASH_FUNCTIONS
from copietje.data import read_db
from copietje.ranking import corpus_from_generator
from experiments.evaluation import get_id_from_uid


here = Path(__file__).parent

output_dir = Path(__file__).parent / 'output'
output_dir.mkdir(parents=True, exist_ok=True)

run_timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
with open(output_dir / f'{run_timestamp}-fp-fn-lsh-experiment.csv', 'w') as f:
    w = csv.writer(f)
    w.writerow(['data size', 'num perms', 'threshold', 'false negative weight', 'bands',
                'f1', 'precision', 'recall',
                'false positive', 'false negative', 'true positive', 'true negative'])

    for num_perms in [64, 128, 256, 512]:
        print('Running corpus generation...')
        hasher = Condenser(tokenizer=tokenize,
                           normalizer=normalize_html,
                           hash_function=HASH_FUNCTIONS['sha1'], permutations=num_perms)
        paths = confidence.load_name('copietje')
        # Add bins to select a subset of the dataset and set n_versions to limit the datapoints per entry
        data_generator = read_db(paths.news_edits_db, bins=None, n_versions=None)
        corpus = corpus_from_generator(data_generator, hasher)

        # Make a dict of {uid: [matched uids]} to contain true positives/expected matches
        true_matches = {uid: {other_uid for other_uid in corpus.keys()
                              if other_uid != uid and get_id_from_uid(uid) == get_id_from_uid(other_uid)}
                        for uid in corpus.keys()}
        total_set_size = len(corpus)

        thresholds = numeric_range(0.3, 1.0, 0.05)

        # From the LSH docstring:
        # `weights` must sum to 1.0, and the format is
        # (false positive weight, false negative weight).
        # For example, if minimizing false negative (or maintaining high recall) is more
        # important, assign more weight toward false negative: weights=(0.4, 0.6).
        # Try to live with a small difference between weights (i.e. < 0.5).
        fn_weights = numeric_range(0.0, 1.0, 0.05)

        for threshold in thresholds:
            for fn_weight in fn_weights:
                true_positives = 0
                true_negatives = 0
                false_positives = 0
                false_negatives = 0

                print(f'Testing LSH with threshold {threshold:.2f} and weight pair '
                      f'(false positive weight: {1.0 - fn_weight:.2f}, false negative weight: {fn_weight:.2f})')
                try:
                    index = MinHashLSH(threshold=threshold, weights=(1.0 - fn_weight, fn_weight), num_perm=num_perms)
                except ValueError as e:
                    print(f'failed to create lsh with {threshold=:.2f}, {fn_weight=:.2f}:', e)
                    w.writerow([total_set_size, num_perms, f'{threshold:.2f}', f'{fn_weight:.2f}', None, None, None, None, None])
                    continue

                for uid, minhash in corpus.items():
                    index.insert(uid, minhash)

                for uid, minhash in corpus.items():
                    results = {result_uid for result_uid in index.query(minhash)
                               if result_uid != uid and minhash.jaccard(corpus[result_uid]) >= threshold}
                    # True positives are the length of the intersection between the returned set from the query and the true set
                    tmp_true_positives = len(results.intersection(true_matches[uid]))
                    true_positives += tmp_true_positives
                    # False negatives is length of expected matches minus the found matches
                    false_negatives += (len(true_matches[uid]) - tmp_true_positives)
                    # False positives are the ones found in the results, but not in the expected matches set
                    tmp_false_positives = len(results.difference(true_matches[uid]))
                    false_positives += tmp_false_positives
                    # True negatives is the total set size, minus uid itself, minus the length of the expected set and minus the
                    # found false positives
                    true_negatives += (total_set_size - 1 - len(true_matches[uid]) - tmp_false_positives)

                precision = true_positives / (true_positives + false_positives)
                recall = true_positives / (true_positives + false_negatives)
                w.writerow([total_set_size, num_perms, f'{threshold:.2f}', f'{fn_weight:.2f}', index.b,
                            f'{2 / (1 / precision + 1 / recall):.4f}', f'{precision:.4f}', f'{recall:.4f}',
                            false_positives, false_negatives, true_positives, true_negatives])
