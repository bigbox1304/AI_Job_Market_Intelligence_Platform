#embedding_service.py
from sentence_transformers import SentenceTransformer


class EmbeddingService:
    _instance = None

    def __new__(cls, model_path="./data/models/embedding_model"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
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