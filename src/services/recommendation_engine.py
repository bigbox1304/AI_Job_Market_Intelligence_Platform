"""Hybrid ranking layer that turns retrieved candidates into recommendations."""

import re
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Set

from src.ml.learning_ranker import LearningRanker


TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9+#./-]*", re.IGNORECASE)
STOP_WORDS = {
    "and", "with", "for", "the", "a", "an", "to", "in", "at", "of",
    "và", "với", "cho", "một", "có", "tại", "ở", "muốn", "tìm", "sang",
    "làm", "việc", "tôi", "mình", "cần", "những", "các",
}


class RecommendationEngine:
    """Rerank FAISS candidates using user intent and preference signals."""

    def __init__(self):
        self.ranker = LearningRanker()

    @property
    def model_version(self) -> str:
        return self.ranker.model_version

    def rank(
        self,
        query: str,
        jobs: List[Dict[str, Any]],
        history_queries: Iterable[str] | None = None,
        behavior_events: Iterable[Dict[str, Any]] | None = None,
    ) -> List[Dict[str, Any]]:
        query_terms = self._tokens(query)
        history_terms = self._tokens(" ".join(history_queries or []))
        behavior_events = list(behavior_events or [])
        ranked = []
        seen_ids: Set[Any] = set()

        for job in jobs:
            job_id = job.get("job_id")
            if job_id in seen_ids:
                continue
            seen_ids.add(job_id)

            searchable = " ".join(
                str(job.get(field) or "")
                for field in ("job_title", "industry", "job_function", "job_level", "city", "skills")
            )
            field_terms = self._tokens(searchable)
            skill_terms = self._tokens(job.get("skills"))
            title_terms = self._tokens(job.get("job_title"))

            semantic = self._score_percent(job.get("score"))
            skill_signal = self._overlap_score(query_terms, skill_terms)
            role_signal = self._overlap_score(query_terms, title_terms)
            history_signal = self._overlap_score(history_terms, field_terms) if history_terms else 0
            behavior_signal, dismiss_penalty = self._behavior_signals(field_terms, behavior_events)
            freshness_signal = self._freshness_score(job.get("created_on"))

            features = {
                "semantic": semantic,
                "skill": skill_signal,
                "role": role_signal,
                "history": history_signal,
                "behavior": behavior_signal,
                "freshness": freshness_signal,
            }
            recommendation_score = self.ranker.score(features)
            recommendation_score -= dismiss_penalty

            enriched = dict(job)
            enriched["recommendation_score"] = round(max(0, min(100, recommendation_score)))
            enriched["recommendation_features"] = {name: round(value, 4) for name, value in features.items()}
            enriched["recommendation_reasons"] = self._reasons(
                job, semantic, skill_signal, role_signal, history_signal, behavior_signal, dismiss_penalty, query_terms, skill_terms
            )
            enriched["recommendation_label"] = self._label(enriched["recommendation_score"])
            ranked.append(enriched)

        return sorted(ranked, key=lambda item: item["recommendation_score"], reverse=True)

    def _freshness_score(self, created_on: Any) -> float:
        if not created_on:
            return 0
        try:
            if isinstance(created_on, datetime):
                created_at = created_on
            else:
                created_at = datetime.fromisoformat(str(created_on).replace("Z", "+00:00"))
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            age_days = max(0, (datetime.now(timezone.utc) - created_at).total_seconds() / 86400)
            return max(0, min(100, 100 * (0.5 ** (age_days / 90))))
        except (TypeError, ValueError, OverflowError):
            return 0

    def _tokens(self, value: Any) -> Set[str]:
        tokens = {match.group(0).lower() for match in TOKEN_RE.finditer(str(value or ""))}
        return {token for token in tokens if token not in STOP_WORDS and len(token) > 1}

    def _score_percent(self, score: Any) -> float:
        try:
            number = float(score or 0)
        except (TypeError, ValueError):
            return 0
        if number <= 1:
            number *= 100
        return max(0, min(100, number))

    def _overlap_score(self, source: Set[str], target: Set[str]) -> float:
        if not source:
            return 0
        return len(source & target) / len(source) * 100

    def _reasons(
        self,
        job: Dict[str, Any],
        semantic: float,
        skill_signal: float,
        role_signal: float,
        history_signal: float,
        behavior_signal: float,
        dismiss_penalty: float,
        query_terms: Set[str],
        skill_terms: Set[str],
    ) -> List[str]:
        reasons = []
        if skill_signal:
            matched = sorted(query_terms & skill_terms)
            reasons.append("Khớp kỹ năng: " + ", ".join(matched[:4]))
        if role_signal:
            reasons.append("Tên vai trò gần với mục tiêu tìm kiếm")
        if history_signal:
            reasons.append("Liên quan đến các tìm kiếm gần đây của bạn")
        if behavior_signal:
            reasons.append("Phù hợp với các job bạn từng xem/lưu/ứng tuyển")
        if dismiss_penalty:
            reasons.append("Đã giảm ưu tiên do tương đồng với nhóm job bạn đã bỏ qua")
        if semantic >= 70:
            reasons.append("Độ tương đồng ngữ nghĩa cao")
        return reasons[:3] or ["Được truy xuất từ nhóm vị trí có độ tương đồng cao"]

    def _behavior_signals(self, job_terms: Set[str], events: List[Dict[str, Any]]) -> tuple[float, float]:
        positive_weights = {"view": 0.5, "save": 2.0, "apply": 3.0}
        positive_total = 0.0
        positive_match = 0.0
        dismiss_total = 0.0
        dismiss_match = 0.0

        for event in events:
            event_terms = self._tokens(" ".join(str(event.get(field) or "") for field in ("job_title", "industry", "job_function", "job_level", "city", "skills")))
            event_type = event.get("event_type")
            if event_type in positive_weights:
                weight = positive_weights[event_type]
                positive_total += weight
                if job_terms & event_terms:
                    positive_match += weight
            elif event_type == "dismiss":
                dismiss_total += 1
                if job_terms & event_terms:
                    dismiss_match += 1

        positive_signal = positive_match / positive_total * 100 if positive_total else 0
        dismiss_penalty = min(25, dismiss_match / dismiss_total * 25) if dismiss_total else 0
        return positive_signal, dismiss_penalty

    def _label(self, score: int) -> str:
        if score >= 80:
            return "Strong recommendation"
        if score >= 60:
            return "Good recommendation"
        return "Explore"
