# src/core/singleton.py

from src.ml.embedding_service import EmbeddingService

# load 1 lần duy nhất
embedding_service = EmbeddingService()