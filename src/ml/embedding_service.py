#embedding_service.py
from sentence_transformers import SentenceTransformer
import os


class EmbeddingService:
    _instance = None

    def __new__(cls, model_path=None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            model_path = model_path or os.getenv("EMBEDDING_MODEL_PATH", "./data/models/embedding_model")
            cls._instance.model = SentenceTransformer(
                model_path,  # ensure local folder
                device="cpu",  # hoặc "cuda" nếu GPU
                local_files_only=True  # <--- bắt buộc để không tải từ HuggingFace
            )
        return cls._instance

    def encode(self, texts):
        return self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=False
        )
