import numpy as np
from typing import Dict, List, Tuple

class LinkPredictionMetrics:
    """
    Computes rigorous link prediction metrics including Hits@K, MRR, and PR-AUC.
    """
    
    @staticmethod
    def _rank_scores(y_true: np.ndarray, y_score: np.ndarray) -> np.ndarray:
        """
        Returns the rank of positive samples.
        Ties are broken deterministically (e.g. by index or average rank).
        We use scipy.stats.rankdata which assigns average rank for ties, but we negate y_score to rank descending.
        """
        from scipy.stats import rankdata
        # rankdata ranks ascending. We want descending, so we negate.
        ranks = rankdata(-y_score, method='average')
        # Filter ranks of the actual positive samples
        pos_ranks = ranks[y_true == 1]
        return pos_ranks

    @staticmethod
    def hits_at_k(y_true: np.ndarray, y_score: np.ndarray, k: int) -> float:
        """
        Calculates the Hits@K metric.
        Proportion of positive edges ranked in the top K.
        """
        if len(y_true) == 0 or sum(y_true) == 0:
            return 0.0
            
        pos_ranks = LinkPredictionMetrics._rank_scores(y_true, y_score)
        hits = np.sum(pos_ranks <= k)
        return float(hits / len(pos_ranks))

    @staticmethod
    def mrr(y_true: np.ndarray, y_score: np.ndarray) -> float:
        """
        Mean Reciprocal Rank (MRR).
        MRR = 1/|pos| sum(1 / rank_i)
        """
        if len(y_true) == 0 or sum(y_true) == 0:
            return 0.0
            
        pos_ranks = LinkPredictionMetrics._rank_scores(y_true, y_score)
        reciprocal_ranks = 1.0 / pos_ranks
        return float(np.mean(reciprocal_ranks))

    @staticmethod
    def pr_auc(y_true: np.ndarray, y_score: np.ndarray) -> float:
        """
        Precision-Recall Area Under Curve.
        """
        if len(y_true) == 0 or sum(y_true) == 0 or sum(y_true) == len(y_true):
            return 0.0
            
        # Sort scores in descending order
        desc_score_indices = np.argsort(y_score, kind="mergesort")[::-1]
        y_score = y_score[desc_score_indices]
        y_true = y_true[desc_score_indices]
        
        # True Positives and False Positives accumulation
        tps = np.cumsum(y_true)
        fps = np.cumsum(1 - y_true)
        
        # Calculate precision and recall
        precision = tps / (tps + fps)
        # Handle division by zero
        precision[np.isnan(precision)] = 0.0
        
        recall = tps / tps[-1]
        
        # Calculate PR-AUC using trapezoidal rule (approximate average precision)
        # For true AP, we sum (R_n - R_{n-1}) * P_n
        recall_diff = np.diff(recall, prepend=0)
        ap = np.sum(recall_diff * precision)
        
        return float(ap)

    @staticmethod
    def compute_all_metrics(y_true: np.ndarray, y_score: np.ndarray) -> Dict[str, float]:
        """
        Computes all standard benchmark metrics.
        """
        # Edge case: no valid scores or all same scores might cause NaN
        if np.isnan(y_score).any():
            y_score = np.nan_to_num(y_score, 0.0)
            
        return {
            "Hits@1": LinkPredictionMetrics.hits_at_k(y_true, y_score, 1),
            "Hits@3": LinkPredictionMetrics.hits_at_k(y_true, y_score, 3),
            "Hits@5": LinkPredictionMetrics.hits_at_k(y_true, y_score, 5),
            "MRR": LinkPredictionMetrics.mrr(y_true, y_score),
            "PR_AUC": LinkPredictionMetrics.pr_auc(y_true, y_score),
        }
