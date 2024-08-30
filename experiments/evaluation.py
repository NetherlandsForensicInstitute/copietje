import re
from pathlib import Path
from statistics import mean, stdev
from typing import Callable, Iterable, List, Tuple


def get_id_from_file_name(file_name: str) -> str:
    """
    The files in our test data contain numbers indicating which texts are the same
    """
    return re.findall(r'\d+', Path(file_name).name)[0]


def get_id_from_uid(uid: str) -> str:
    """
    For the News Edit data, the uid is formatted as '[db_name]_[entry_id]_[version number]'.
    The entry_id refers to two texts being the same article, if they're from the same db.
    '[db_name]_[entry_id]' would thus give an article ID
    """
    return f"{uid.split('_')[0]}_{uid.split('_')[1]}"


class Evaluator:
    def __init__(self, id_parser: Callable[[str], str]):
        self.id_parser = id_parser

    def mean_at_k(self, rank_matrix: Iterable[Tuple[str, List[Tuple[float, str]]]],
                  at_k_function: Callable[[List[int], int], float],
                  k: int = 10) -> float:
        mean_scores = []
        for document, scores in rank_matrix:
            file_id = self.id_parser(document)
            scores.sort(reverse=True)
            y_true = [int(file_id == self.id_parser(sim_name)) for _, sim_name in scores]
            mean_scores.append(at_k_function(y_true, k))
        return mean(mean_scores)

    def precision_at_k(self, y_true, k: int = 10) -> float:
        """Fraction of how many relevant items were found in the first k items"""
        return sum(y_true[:k]) / k

    def mean_precision_at_k(self, rank_matrix: Iterable[Tuple[str, List[Tuple[float, str]]]],
                            k: int = 10) -> float:
        """Average fraction of how many relevant items were found in the first k items for all data"""
        return self.mean_at_k(rank_matrix, self.precision_at_k, k)

    def recall_at_k(self, y_true, k: int = 10):
        """How many relevant items were found in the first k items vs. all relevant items"""
        return (sum(y_true[:k]) / sum(y_true)) if sum(y_true) > 0 else 0

    def mean_recall_at_k(self, rank_matrix: Iterable[Tuple[str, List[Tuple[float, str]]]],
                         k: int = 10) -> float:
        """On average, how many relevant items were found in the first k items vs. all relevant items"""
        return self.mean_at_k(rank_matrix, self.recall_at_k, k)

    def reciprocal_rank(self, y_true: List[int]):
        """Measure of how high up in the ranking the first correct match was found"""
        return (1 / (y_true.index(1) + 1)) if (y_true.index(1) + 1) > 0 else 0

    def mean_reciprocal_rank(self, rank_matrix: Iterable[Tuple[str, List[Tuple[float, str]]]]) -> float:
        """Average measure of how high up in the ranking the first correct match was found"""
        mean_scores = []
        for document, scores in rank_matrix:
            file_id = self.id_parser(document)
            scores.sort(reverse=True)
            y_true = [int(file_id == self.id_parser(sim_name)) for _, sim_name in scores if document != sim_name]
            mean_scores.append(self.reciprocal_rank(y_true))
        return mean(mean_scores)

    def all_evaluation_functions(self, rank_matrix: Iterable[Tuple[str, List[Tuple[float, str]]]],
                                 k: int = 10) -> tuple[float, float, float, float, float, float, float]:
        """
        Calculate the precision@k, recall@k, mrr, avg score + stdev of first match and avg score + stdev of first non
          match in the same loop through the rank matrix

        If there are no matches in the data (i.e. y_true is always a list of zeros), then the mean precision,
        mean recall, mrr, and first match are set to 99.

        return: mean precision@k, mean recall@k, mean mrr, avg score first match, stdev score first match,
            avg score first non-match, stdev score first non match
        """
        all_precision_at_k = []
        all_recall_at_k = []
        all_mrr = []
        all_first_match = []
        all_first_non_match = []
        for document, scores in rank_matrix:
            file_id = self.id_parser(document)
            scores = sorted(scores, reverse=True)
            y_true = [int(file_id == self.id_parser(sim_name)) for _, sim_name in scores if document != sim_name]
            y_values = [score for score, sim_name in scores if document != sim_name]

            # Only calculate metrics if there are any matches for the data
            if sum(y_true) > 0:
                all_precision_at_k.append(self.precision_at_k(y_true, k))
                all_recall_at_k.append(self.recall_at_k(y_true, k))
                all_mrr.append(self.reciprocal_rank(y_true))
                all_first_match.append(self.first_match(y_true, y_values))

            # First non-match can always be found
            all_first_non_match.append(self.first_non_match(y_true, y_values))
        for l in [all_precision_at_k, all_recall_at_k, all_mrr, all_first_match, all_first_non_match]:
            if len(l) == 0:
                l += [99, 99]
        return (mean(all_precision_at_k), mean(all_recall_at_k), mean(all_mrr), mean(all_first_match),
                stdev(all_first_match), mean(all_first_non_match), stdev(all_first_non_match))

    def first_match(self, y_true: List[int], values: List[float]):
        return values[y_true.index(1)]

    def first_non_match(self, y_true, values: List[float]):
        return values[y_true.index(0)]

    def jaccard_estimation_error(self, minhash_matrix: Iterable[Tuple[str, List[Tuple[float, str]]]],
                                 jaccard_matrix: Iterable[Tuple[str, List[Tuple[float, str]]]]):
        """
        Calculates the mean jaccard estimation error on the complete dataset as the average of the absolute difference of
        'minhash jaccard' and 'full jaccard' per document
        """
        all_errors = []
        for minhash, jaccard in zip(sorted(minhash_matrix), sorted(jaccard_matrix)):
            for minhash_jaccard, full_jaccard in zip(sorted(minhash[1], key=lambda x: x[1]),
                                                     sorted(jaccard[1], key=lambda x: x[1])):
                all_errors.append(abs(minhash_jaccard[0] - full_jaccard[0]))
        return mean(all_errors)
