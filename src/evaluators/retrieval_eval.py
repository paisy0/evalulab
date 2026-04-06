from __future__ import annotations

import math

from src.config import thresholds

__all__ = ["run_retrieval_eval", "precision_at_k", "recall_at_k", "ndcg_at_k"]


def precision_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    if k <= 0:
        return 0.0
    top_k = list(dict.fromkeys(retrieved[:k]))
    return sum(1 for doc in top_k if doc in relevant) / k


def recall_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    if not relevant:
        return 0.0
    top_k = list(dict.fromkeys(retrieved[:k]))
    return sum(1 for doc in top_k if doc in relevant) / len(relevant)


def ndcg_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    top_k = list(dict.fromkeys(retrieved[:k]))
    dcg = sum(
        1.0 / math.log2(i + 2)
        for i, doc in enumerate(top_k)
        if doc in relevant
    )
    ideal = sum(
        1.0 / math.log2(i + 2)
        for i in range(min(len(relevant), k))
    )
    return dcg / ideal if ideal > 0 else 0.0


def run_retrieval_eval(
    query: str,
    retrieved: list[str],
    relevant: list[str],
    k: int = 5,
    precision_threshold: float | None = None,
    recall_threshold: float | None = None,
    ndcg_threshold: float | None = None,
) -> dict:
    p_min = thresholds.precision_min if precision_threshold is None else precision_threshold
    r_min = thresholds.recall_min if recall_threshold is None else recall_threshold
    n_min = thresholds.ndcg_min if ndcg_threshold is None else ndcg_threshold
    relevant_set = set(relevant)

    p = precision_at_k(retrieved, relevant_set, k)
    r = recall_at_k(retrieved, relevant_set, k)
    n = ndcg_at_k(retrieved, relevant_set, k)

    return {
        "query": query,
        "precision_k": round(p, 4),
        "recall_k": round(r, 4),
        "ndcg_k": round(n, 4),
        "k": k,
        "passed": p >= p_min and r >= r_min and n >= n_min,
    }