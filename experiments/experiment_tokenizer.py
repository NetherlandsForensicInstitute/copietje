from datetime import datetime
from pathlib import Path

from tabulate import tabulate

from copietje import Condenser, normalize
from experiments.data import read_directory
from copietje.ranking import score_matrix, corpus_from_generator
from copietje.tokenizers import TOKENIZERS


here = Path(__file__).parent
(here / 'output').mkdir(parents=True, exist_ok=True)


run_timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
done = set()
with open(here / f"output/{run_timestamp}-tokenizer-experiment.txt", 'w') as f:
    # test all tokenizers
    for experiment_name, tokenizer in TOKENIZERS.items():
        # TOKENIZERS contains duplicates for convenience, that is inconvenient for this experiment, so track the
        # tokenizers we've already used
        if tokenizer in done:
            continue
        done.add(tokenizer)

        hasher = Condenser(tokenizer=tokenizer,
                           normalizer=normalize)
        corpus = corpus_from_generator(read_directory(here / "../resources/test_data"), hasher)
        # sort corpus so that our documentation is nicely in order
        corpus = dict(sorted(corpus.items()))
        matrix = score_matrix(corpus)

        # write the results for each tokenizer to file
        f.writelines((
            # a header with the name of the tokenizer
            experiment_name, '\n',
            '-' * len(experiment_name), '\n\n',
            # a result table with the file names of the corpus as header and the scores as the rows
            tabulate(
                headers=[doc.stem for doc in corpus.keys()],
                tabular_data=[[score[0] for score in row[1]]  # every row is (id, [(score, id)]), we want only scores
                              for row in matrix],
                maxheadercolwidths=16,
                floatfmt='.3f',
            ), '\n\n',
        ))
