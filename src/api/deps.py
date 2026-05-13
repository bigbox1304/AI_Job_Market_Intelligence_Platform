#deps.py
from fastapi import Depends
from src.core.database import get_db, release_db
from src.repositories.job_repository import JobRepository
from src.services.job_service import JobService
from src.services.recommend_service import RecommendService
from src.ml.faiss_service import FaissService
from src.ml.embedding_service import EmbeddingService
from src.repositories.search_history_repository import SearchHistoryRepository
from src.services.search_history_service import SearchHistoryService

# =========================================
# DB
# =========================================
def get_db_dep():
    conn = get_db()
    try:
        yield conn
    finally:
        release_db(conn)

# =========================================
# JOB SERVICE
# =========================================
def get_job_service(conn = Depends(get_db_dep)):
    repo = JobRepository(conn)
    return JobService(repo)
# =========================================
# RECOMMEND SERVICE
# =========================================
def get_recommend_service(conn = Depends(get_db_dep)):
    repo = JobRepository(conn)

    faiss_service = FaissService()
    embedding_service = EmbeddingService()

    return RecommendService(
        job_repository=repo,
        faiss_service=faiss_service,
        embedding_service=embedding_service
    )



def get_history_service(conn = Depends(get_db_dep)):
    repo = SearchHistoryRepository(conn)
    return SearchHistoryService(repo)