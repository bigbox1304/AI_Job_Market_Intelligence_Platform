"""Small executable example for validating ranking metrics during development."""

from src.evaluation.ranking_metrics import evaluate_rankings


if __name__ == "__main__":
    sample_cases = [
        {"relevant_job_ids": [2, 4], "ranked_job_ids": [2, 1, 4, 8]},
        {"relevant_job_ids": [5], "ranked_job_ids": [1, 3, 5]},
    ]
    print(evaluate_rankings(sample_cases, k=3))
