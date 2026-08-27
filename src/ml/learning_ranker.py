"""Small pairwise ranker with a deterministic hybrid fallback.

The model is intentionally dependency-light: it can be trained with NumPy and
loaded by the API without introducing a second ML serving stack.
"""

import json
import math
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List

import numpy as np


FEATURE_NAMES = ("semantic", "skill", "role", "history", "behavior", "freshness")
DEFAULT_WEIGHTS = {
    "semantic": 0.45,
    "skill": 0.25,
    "role": 0.15,
    "history": 0.10,
    "behavior": 0.10,
    "freshness": 0.05,
}


class LearningRanker:
    def __init__(self, model_path: str | None = None):
        self.model_path = Path(model_path or os.getenv("RANKER_MODEL_PATH", "data/models/ranker.json"))
        self.weights = dict(DEFAULT_WEIGHTS)
        self.model_version = os.getenv("RECOMMENDATION_MODEL_VERSION", "hybrid-v1")
        self._load()

    def _load(self) -> None:
        if not self.model_path.exists():
            return
        try:
            payload = json.loads(self.model_path.read_text(encoding="utf-8"))
            loaded = payload.get("weights", {})
            if all(name in loaded for name in FEATURE_NAMES):
                self.weights = {name: float(loaded[name]) for name in FEATURE_NAMES}
                self.model_version = payload.get("model_version", "learned-ranker-v1")
        except (OSError, ValueError, TypeError):
            # A bad optional model must never prevent recommendation serving.
            return

    def score(self, features: Dict[str, float]) -> float:
        total_weight = sum(max(0, weight) for weight in self.weights.values()) or 1
        weighted = sum(
            max(0, float(features.get(name, 0))) * max(0, self.weights.get(name, 0))
            for name in FEATURE_NAMES
        )
        return max(0, min(100, weighted / total_weight))

    def train_pairwise(
        self,
        rows: Iterable[Dict[str, Any]],
        epochs: int = 120,
        learning_rate: float = 0.05,
        l2: float = 0.001,
    ) -> Dict[str, float]:
        samples = list(rows)
        positives = [self._vector(row["features"]) for row in samples if int(row.get("label", 0)) == 1]
        negatives = [self._vector(row["features"]) for row in samples if int(row.get("label", 0)) == 0]
        if not positives or not negatives:
            raise ValueError("Pairwise training needs both positive and negative examples")

        weights = np.array([self.weights[name] for name in FEATURE_NAMES], dtype=float)
        for _ in range(epochs):
            for positive in positives:
                for negative in negatives:
                    difference = positive - negative
                    margin = float(np.dot(weights, difference))
                    probability = 1 / (1 + math.exp(-max(-30, min(30, margin))))
                    weights += learning_rate * ((1 - probability) * difference - l2 * weights)

        weights = np.maximum(weights, 0)
        if weights.sum() == 0:
            weights = np.array([DEFAULT_WEIGHTS[name] for name in FEATURE_NAMES])
        weights = weights / weights.sum()
        self.weights = {name: round(float(weights[index]), 6) for index, name in enumerate(FEATURE_NAMES)}
        return self.weights

    def save(self, path: str | None = None, model_version: str = "learned-ranker-v1") -> Path:
        output = Path(path or self.model_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps({
            "model_version": model_version,
            "features": list(FEATURE_NAMES),
            "weights": self.weights,
        }, indent=2), encoding="utf-8")
        return output

    def _vector(self, features: Dict[str, Any]) -> np.ndarray:
        return np.array([float(features.get(name, 0)) / 100 for name in FEATURE_NAMES], dtype=float)
