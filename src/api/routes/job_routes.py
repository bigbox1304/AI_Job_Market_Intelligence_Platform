#job_routes.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional

from src.services.job_service import JobService
from src.api.deps import get_job_service

router = APIRouter()


# =========================================
# 1. GET JOB BY ID
# =========================================
@router.get("/{job_id:int}")
def get_job(
    job_id: int,
    service: JobService = Depends(get_job_service)
):
    job = service.get_job_by_id(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return job


# =========================================
# 2. SEARCH JOB (basic)
# =========================================
@router.get("/search")
def search_jobs(
    q: str = Query(..., description="Search keyword"),
    limit: int = Query(20, ge=1, le=100),
    service: JobService = Depends(get_job_service)
):
    results = service.search_jobs(q, limit)
    return {
        "query": q,
        "count": len(results),
        "results": results
    }


# =========================================
# 3. FILTER JOB (optional nâng cao nhẹ)
# =========================================
@router.get("/filter")
def filter_jobs(
    city: Optional[str] = None,
    level: Optional[str] = None,
    industry: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    service: JobService = Depends(get_job_service)
):
    results = service.filter_jobs(
        city=city,
        level=level,
        industry=industry,
        limit=limit
    )

    return {
        "filters": {
            "city": city,
            "level": level,
            "industry": industry
        },
        "count": len(results),
        "results": results
    }
