#job_service.py
from typing import List, Optional, Dict
from src.repositories.job_repository import JobRepository


class JobService:
    def __init__(self, repo: JobRepository):
        self.repo = repo

    # =========================================
    # 1. GET JOB BY ID
    # =========================================
    def get_job_by_id(self, job_id: int) -> Optional[Dict]:
        job = self.repo.get_by_id(job_id)
        return job

    # =========================================
    # 2. SEARCH JOB (KEYWORD)
    # =========================================
    def search_jobs(self, query: str, limit: int = 20) -> List[Dict]:
        if not query or len(query.strip()) == 0:
            return []

        results = self.repo.search(query.strip(), limit)
        return results

    # =========================================
    # 3. FILTER JOB
    # =========================================
    def filter_jobs(
        self,
        city: Optional[str] = None,
        level: Optional[str] = None,
        industry: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict]:

        results = self.repo.filter(
            city=city,
            level=level,
            industry=industry,
            limit=limit
        )

        return results

    # =========================================
    # 4. GET MULTIPLE JOBS (CHO RECOMMEND)
    # =========================================
    def get_jobs_by_ids(self, job_ids: List[int]) -> List[Dict]:
        if not job_ids:
            return []

        jobs = self.repo.get_by_ids(job_ids)

        # giữ thứ tự theo FAISS trả về
        job_map = {job["job_id"]: job for job in jobs}
        ordered_jobs = [job_map[jid] for jid in job_ids if jid in job_map]

        return ordered_jobs