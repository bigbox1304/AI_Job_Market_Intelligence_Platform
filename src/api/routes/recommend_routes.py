#recommend_routes.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from pydantic import BaseModel

from src.services.recommend_service import RecommendService
from src.api.deps import get_recommend_service
from fastapi import Request
from src.api.deps import get_history_service
from src.services.search_history_service import SearchHistoryService
router = APIRouter()
from fastapi import BackgroundTasks
from src.core.redis import cache_get
import hashlib


# =========================================
# REQUEST MODELS
# =========================================
class RecommendRequest(BaseModel):
    text: str
    top_k: int = 10
    offset: int = 0

class RecommendFilterRequest(BaseModel):
    text: str
    city: Optional[str] = None
    level: Optional[str] = None
    top_k: int = 10

class RecommendAnalyticsRequest(BaseModel):
    text: str
    top_k: int = 100

# =========================================
# 1. RECOMMEND BY TEXT
# =========================================
@router.post("/")
def recommend_jobs(
    req: RecommendRequest,
    service: RecommendService = Depends(get_recommend_service)
):
    results = service.recommend_by_query(req.text, req.top_k)

    return {
        "query": req.text,
        "count": len(results),
        "results": results
    }


# =========================================
# 2. SIMILAR JOBS
# =========================================
@router.get("/job/{job_id}")
def recommend_similar_jobs(
    job_id: int,
    top_k: int = Query(10, ge=1, le=50),
    service: RecommendService = Depends(get_recommend_service)
):
    results = service.recommend_by_job(job_id, top_k)

    if not results:
        raise HTTPException(status_code=404, detail="No similar jobs")

    return {
        "job_id": job_id,
        "count": len(results),
        "results": results
    }


# =========================================
# 3. HYBRID (FILTER)
# =========================================
@router.post("/filter")
def recommend_with_filter(
    req: RecommendFilterRequest,
    service: RecommendService = Depends(get_recommend_service)
):
    results = service.recommend_with_filter(
        query=req.text,
        city=req.city,
        level=req.level,
        top_k=req.top_k
    )

    return {
        "query": req.text,
        "filters": {
            "city": req.city,
            "level": req.level
        },
        "count": len(results),
        "results": results
    }
@router.post("/analytics")
def recommend_with_analytics(
    req: RecommendAnalyticsRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    service: RecommendService = Depends(get_recommend_service),
    history_service: SearchHistoryService = Depends(get_history_service)
):
    try:
        result = service.recommend_without_llm(
            query=req.text,
            top_k=req.top_k
        )

        user = getattr(request.state, "user", None)
        if user:
            history_service.save_history(
                user_email=user["sub"],
                query=req.text,
                filters={}
            )

        background_tasks.add_task(
            service.generate_llm_summary_async,
            req.text,
            result["analytics"]
        )

        return result

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}
@router.get("/personalized")
def personalized_recommend(
    request: Request,
    service: RecommendService = Depends(get_recommend_service),
    history_service: SearchHistoryService = Depends(get_history_service)
):
    user = getattr(request.state, "user", None)

    if not user:
        return {
            "suggested_keywords": [],
            "jobs": []
        }

    history = history_service.get_history(user.get("sub"))

    if not history:
        return {
            "suggested_keywords": [],
            "jobs": []
        }

    # lấy keyword từ history
    import re

    queries = []

    for h in history:
        tokens = re.split(r"[,\s;/|]+", h["query"].lower())
        queries.extend(tokens)

    # remove rỗng
    queries = [q for q in queries if q]

    # lấy 3 query gần nhất
    query = " ".join(queries[:3])

    jobs = service.recommend_by_query(query, top_k=10)

    return {
        "suggested_keywords": queries[:5],
        "jobs": jobs
    }

@router.get("/summary")
def get_summary(query: str):

    normalized_query = query.strip().lower()
    cache_key = f"llm:{hashlib.md5(normalized_query.encode()).hexdigest()}"

    summary = cache_get(cache_key)

    return {"summary": summary}