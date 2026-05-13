#recommend_service.py
from typing import List, Dict, Optional
import numpy as np
from src.services.job_service import JobService
from src.ml.embedding_service import EmbeddingService
from src.ml.faiss_service import FaissService
from src.services.analytics_service import AnalyticsService
from functools import lru_cache
from src.ml.ollama_service import OllamaService
from src.services.llm_prompt_service import LLMPromptService
from src.core.redis import cache_get, cache_set
import hashlib

@lru_cache(maxsize=128)
def cached_encode(text: str):
    from src.core.singleton import embedding_service
    return embedding_service.encode([text])[0]

class RecommendService:
    def __init__(self, job_repository, faiss_service, embedding_service):
        self.job_repository = job_repository
        self.faiss_service = faiss_service
        self.embedding_service = embedding_service
        self.analytics_service = AnalyticsService()
        self.ollama_service = OllamaService()
        self.prompt_service = LLMPromptService()

    # =========================================
    # 1. QUERY → RECOMMEND
    # =========================================
    def recommend_by_query(self, query: str, top_k: int = 10) -> List[Dict]:

        if not query or not query.strip():
            return []

        # encode query
        query_vector = cached_encode(query)

        # normalize (rất quan trọng)
        query_vector = self._normalize(query_vector)

        # search FAISS
        scores, indices = self.faiss_service.search(query_vector, top_k)

        job_ids = self.faiss_service.get_job_ids(indices)

        # query DB
        jobs = self.job_repository.get_jobs_by_ids(job_ids[:top_k])

        # attach score
        return self._attach_scores(jobs, job_ids, scores)

    # =========================================
    # 2. JOB → SIMILAR JOBS
    # =========================================
    def recommend_by_job(self, job_id: int, top_k: int = 10) -> List[Dict]:

        vector = self.faiss_service.get_vector_by_job_id(job_id)

        if vector is None:
            return []

        vector = self._normalize(vector)

        scores, indices = self.faiss_service.search(vector, top_k + 1)

        job_ids = self.faiss_service.get_job_ids(indices)

        # remove itself
        job_ids = [jid for jid in job_ids if jid != job_id][:top_k]

        jobs = self.job_repository.get_jobs_by_ids(job_ids)

        return self._attach_scores(jobs, job_ids, scores)

    # =========================================
    # 3. HYBRID FILTER
    # =========================================
    def recommend_with_filter(
        self,
        query: str,
        city: Optional[str] = None,
        level: Optional[str] = None,
        top_k: int = 10
    ) -> List[Dict]:

        # lấy rộng ra để filter
        candidates = self.recommend_by_query(query, top_k=50)

        results = []

        for job in candidates:
            if city and job.get("city") != city:
                continue

            if level and job.get("job_level") != level:
                continue

            results.append(job)

            if len(results) >= top_k:
                break

        return results

    # =========================================
    # UTILS
    # =========================================
    def _normalize(self, vector: np.ndarray) -> np.ndarray:
        norm = np.linalg.norm(vector)
        if norm == 0:
            return vector
        return vector / norm

    def _attach_scores(
        self,
        jobs: List[Dict],
        job_ids: List[int],
        scores
    ) -> List[Dict]:

        if scores is None:
            return jobs

        score_map = {
            job_ids[i]: float(scores[i])
            for i in range(len(job_ids))
        }

        for job in jobs:
            job["score"] = score_map.get(job["job_id"])

        return jobs
    # =========================================
    # RECOMMEND + ANALYTICS
    # =========================================
    def recommend_with_analytics(self, query: str, top_k: int = 10):
        
        normalized_query = query.strip().lower()
        cache_key = f"recommend:{hashlib.md5(normalized_query.encode()).hexdigest()}:{top_k}"
        cached = cache_get(cache_key)
        if cached:
            print("🔥 REDIS CACHE HIT")
            return cached

        jobs = self.recommend_by_query(query, top_k)

        insights = self.analytics_service.analyze(jobs)

        prompt = self.prompt_service.build_market_prompt(
            query,
            insights
        )

        ai_summary = self.ollama_service.generate(prompt)

        result = {
            "query": query,
            "count": len(jobs),
            "results": jobs,
            "analytics": insights,
            "ai_summary": ai_summary
        }

        cache_set(cache_key, result, ttl=300)

        return result  
    # =========================================
    # FAST (NO LLM)
    # =========================================
    def recommend_without_llm(self, query: str, top_k: int = 10):

        jobs = self.recommend_by_query(query, top_k)
        insights = self.analytics_service.analyze(jobs)

        return {
            "query": query,
            "count": len(jobs),
            "results": jobs,
            "analytics": insights,
            "ai_summary": None
        }


    # =========================================
    # BACKGROUND LLM
    # =========================================
    def generate_llm_summary_async(self, query, analytics):

        normalized_query = query.strip().lower()
        cache_key = f"llm:{hashlib.md5(normalized_query.encode()).hexdigest()}"

        # nếu đã có thì bỏ
        if cache_get(cache_key):
            return

        prompt = self.prompt_service.build_market_prompt(
            query,
            analytics
        )

        ai_summary = self.ollama_service.generate(prompt)

        cache_set(cache_key, ai_summary, ttl=3600)