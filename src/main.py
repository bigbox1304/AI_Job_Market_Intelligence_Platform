# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import ORJSONResponse
from src.middleware.auth_middleware import AuthMiddleware
import os


# import routers
from src.api.routes.job_routes import router as job_router
from src.api.routes.recommend_routes import router as recommend_router
from src.api.routes.auth_google_routes import router as google_auth_router
from starlette.middleware.sessions import SessionMiddleware
from src.api.routes.history_routes import router as history_router
from src.api.routes.event_routes import router as event_router

# =========================================
# INIT APP (ORJSON)
# =========================================

app = FastAPI(
    title="Job Recommendation API",
    description="API tư vấn nghề nghiệp sử dụng FAISS + NLP",
    version="1.0.0",
    default_response_class=ORJSONResponse   # ⚡ faster JSON
)


# =========================================
# GZIP COMPRESSION
# =========================================

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET", os.getenv("SECRET_KEY", "dev-only-change-me"))
)

app.add_middleware(
    GZipMiddleware,
    minimum_size=1000  # chỉ nén nếu response > 1KB
)


# =========================================
# CORS (CHO FRONTEND)
# =========================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in os.getenv("CORS_ORIGINS", "http://localhost:8501").split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(AuthMiddleware)
# =========================================
# REGISTER ROUTES
# =========================================

app.include_router(
    job_router,
    prefix="/jobs",
    tags=["Jobs"]
)

app.include_router(
    recommend_router,
    prefix="/recommend",
    tags=["Recommend"]
)


# =========================================
# ROOT
# =========================================

@app.get("/")
def root():
    return {
        "message": "Job Recommendation API is running",
        "docs": "/docs"
    }


# =========================================
# HEALTH CHECK
# =========================================

@app.get("/health")
def health_check():
    return {"status": "ok"}

app.include_router(
    google_auth_router,
    prefix="/auth",
    tags=["Auth"]
)

app.include_router(
    history_router,
    prefix="/history",
    tags=["History"]
)

app.include_router(
    event_router,
    prefix="/events",
    tags=["Behavior Events"]
)

# =========================================
# START (OPTIONAL)
# =========================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
