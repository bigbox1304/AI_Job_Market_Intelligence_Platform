import math
from typing import Any, Dict, Iterable, List, Sequence, Set


def _relevant_set(relevant_ids: Iterable[Any]) -> Set[Any]:
    return set(relevant_ids)


def precision_at_k(ranked_ids: Sequence[Any], relevant_ids: Iterable[Any], k: int = 10) -> float:
    if k <= 0:
        return 0.0
    top_k = list(ranked_ids[:k])
    if not top_k:
        return 0.0
    relevant = _relevant_set(relevant_ids)
    return sum(item in relevant for item in top_k) / len(top_k)


def recall_at_k(ranked_ids: Sequence[Any], relevant_ids: Iterable[Any], k: int = 10) -> float:
    relevant = _relevant_set(relevant_ids)
    if not relevant:
        return 0.0
    return sum(item in relevant for item in ranked_ids[:k]) / len(relevant)


def reciprocal_rank(ranked_ids: Sequence[Any], relevant_ids: Iterable[Any]) -> float:
    relevant = _relevant_set(relevant_ids)
    for index, item in enumerate(ranked_ids, start=1):
        if item in relevant:
            return 1.0 / index
    return 0.0


def ndcg_at_k(ranked_ids: Sequence[Any], relevant_ids: Iterable[Any], k: int = 10) -> float:
    relevant = _relevant_set(relevant_ids)
    if not relevant:
        return 0.0
    dcg = sum(
        (1.0 / math.log2(index + 2))
        for index, item in enumerate(ranked_ids[:k])
        if item in relevant
    )
    ideal_hits = min(len(relevant), k)
    ideal_dcg = sum(1.0 / math.log2(index + 2) for index in range(ideal_hits))
    return dcg / ideal_dcg if ideal_dcg else 0.0


def evaluate_rankings(cases: Iterable[Dict[str, Any]], k: int = 10) -> Dict[str, float]:
    cases = list(cases)
    if not cases:
        return {"precision_at_k": 0.0, "recall_at_k": 0.0, "mrr": 0.0, "ndcg_at_k": 0.0}

    metrics = {"precision_at_k": 0.0, "recall_at_k": 0.0, "mrr": 0.0, "ndcg_at_k": 0.0}
    valid_cases = 0
    for case in cases:
        relevant = case.get("relevant_job_ids", [])
        if not relevant:
            continue
        ranked = case.get("ranked_job_ids", [])
        metrics["precision_at_k"] += precision_at_k(ranked, relevant, k)
        metrics["recall_at_k"] += recall_at_k(ranked, relevant, k)
        metrics["mrr"] += reciprocal_rank(ranked, relevant)
        metrics["ndcg_at_k"] += ndcg_at_k(ranked, relevant, k)
        valid_cases += 1

    if not valid_cases:
        return metrics
    return {name: round(value / valid_cases, 4) for name, value in metrics.items()}
