from datetime import datetime
from pathlib import Path
from time import perf_counter

import confidence

from copietje import Condenser, normalize_html, tokenize, HASH_FUNCTIONS
from copietje.ranking import score_matrix, corpus_from_generator, full_jaccard_matrix, full_token_set_from_generator
from experiments.data import read_db
from experiments.evaluation import Evaluator, get_id_from_uid


here = Path(__file__).parent

output_dir = Path(__file__).parent / 'output'
output_dir.mkdir(parents=True, exist_ok=True)

k = 5
run_timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
with open(output_dir / f"{run_timestamp}-hash-experiment.csv", 'w') as f:
    f.writelines(f"hash type,data size,runtime,precision@{k},recall@{k},mean reciprocal rank,mean first match,"
                 "std first match,mean first non-match,std first non-match,jaccard estimation error\n")


results = []
# test different hash functions
for hash_name, hash_function in HASH_FUNCTIONS.items():
    if not hash_name:
        # one of the entries is the default, with an empty name, that will have been used *with* its name
        continue

    print(f"Testing '{hash_name}' hash")
    hasher = Condenser(tokenizer=tokenize,
                       normalizer=normalize_html,
                       hash_function=hash_function)

    print("Running corpus generation...")
    start_time = perf_counter()
    paths = confidence.load_name('copietje')
    # Add bins to select a larger dataset and set n_versions to a higher number to get more datapoints per entry
    data_generator = read_db(paths['news-edit-db-path'], None, None)
    corpus = corpus_from_generator(data_generator, hasher)
    run_time = round(perf_counter() - start_time)
    print(f"Took {run_time}s")

    # Calculate the precision@k, recall@k, mrr, first match metrics, first non-match metrics
    print("Running evaluation metrics...")
    minhash_matrix = score_matrix(corpus)
    evaluator = Evaluator(get_id_from_uid)
    precision, recall, mrr, avg_match, std_match, avg_non_match, std_non_match = (
        evaluator.all_evaluation_functions(minhash_matrix, k))

    # Calculate the jaccard estimation error
    start_time = perf_counter()
    print("Running full jaccard...")

    minhash_matrix = score_matrix(corpus)
    data_generator = read_db(paths['news-edit-db-path'], None, None)
    jaccard_corpus = full_token_set_from_generator(data_generator, hasher)
    jaccard_matrix = full_jaccard_matrix(jaccard_corpus)
    jaccard_error = evaluator.jaccard_estimation_error(minhash_matrix, jaccard_matrix)
    print(f"Took {round(perf_counter() - start_time, 4)}s")

    line = [hash_name, len(corpus), run_time, precision, recall, mrr, avg_match, std_match, avg_non_match,
            std_non_match, jaccard_error]

    with open(output_dir / f"{run_timestamp}-hash-experiment.csv", 'a') as f:
        f.writelines(','.join([str(i) for i in line]) + '\n')
